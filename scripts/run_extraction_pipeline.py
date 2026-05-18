"""ESG数据提取流水线 — 预处理 + 提取 + 入库

只处理数据库中 extraction_status='pending' 的报告。
"""

import csv
import json
import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

# 项目路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "data" / "esg_data.db"
PDF_DIR = BASE_DIR / "data" / "pdfs"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"
OUTPUT_DIR = BASE_DIR / "data" / "output"

EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# 费用控制
MAX_BUDGET_YUAN = 80.0
COST_PER_1K_INPUT = 0.002
COST_PER_1K_OUTPUT = 0.008

CHUNK_SIZE = 8000
CHUNK_OVERLAP = 500

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class CostTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0
        self.errors = 0

    def record(self, input_tokens, output_tokens):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += (
            input_tokens * COST_PER_1K_INPUT / 1000
            + output_tokens * COST_PER_1K_OUTPUT / 1000
        )
        self.call_count += 1

    def record_error(self):
        self.errors += 1

    @property
    def remaining_budget(self):
        return MAX_BUDGET_YUAN - self.total_cost

    def can_continue(self):
        return self.remaining_budget > 1.0

    def summary(self):
        return (
            f"API调用: {self.call_count}次 | "
            f"输入: {self.total_input_tokens/1000:.1f}K | "
            f"输出: {self.total_output_tokens/1000:.1f}K | "
            f"费用: {self.total_cost:.4f}元 | "
            f"剩余: {self.remaining_budget:.2f}元"
        )


cost_tracker = CostTracker()


# ========== 第1步：PDF预处理 ==========

def preprocess_pdf(pdf_path):
    """将PDF转换为Markdown文本"""
    import pdfplumber

    parts = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                parts.append(f"--- 第{i+1}页 ---")
                text = page.extract_text()
                if text:
                    parts.append(text)
                tables = page.extract_tables()
                if tables:
                    for t_idx, table in enumerate(tables):
                        if not table or len(table) < 2:
                            continue
                        md_table = _table_to_markdown(table)
                        if md_table:
                            parts.append(f"\n[表格 {t_idx+1}]\n{md_table}")
    except Exception as e:
        logger.error(f"pdfplumber失败 {pdf_path.name}: {e}")
        return _extract_fallback(pdf_path)

    return "\n\n".join(parts)


def _extract_fallback(pdf_path):
    import fitz
    parts = []
    try:
        doc = fitz.open(str(pdf_path))
        for i, page in enumerate(doc):
            parts.append(f"--- 第{i+1}页 ---")
            text = page.get_text()
            if text:
                parts.append(text)
        doc.close()
    except Exception as e:
        logger.error(f"PyMuPDF也失败 {pdf_path.name}: {e}")
        return ""
    return "\n\n".join(parts)


def _table_to_markdown(table):
    if not table or len(table) < 2:
        return ""
    clean = []
    for row in table:
        clean.append([str(c).strip().replace("\n", " ") if c else "" for c in row])
    lines = []
    header = clean[0]
    lines.append("| " + " | ".join(h for h in header if h) + " |")
    lines.append("|" + "|".join(["---" for _ in header]) + "|")
    for row in clean[1:]:
        if any(cell for cell in row):
            lines.append("| " + " | ".join(cell for cell in row) + " |")
    return "\n".join(lines)


def run_preprocess(pending_reports):
    """预处理所有待处理的PDF"""
    logger.info(f"=== 第1步：PDF预处理 ({len(pending_reports)}个) ===")
    processed = 0
    skipped = 0
    for i, rep in enumerate(pending_reports):
        stock_code = rep["stock_code"]
        year = rep["year"]
        pdf_path = rep["pdf_path"]

        if not pdf_path:
            continue

        full_pdf_path = BASE_DIR / pdf_path
        if not full_pdf_path.exists():
            logger.warning(f"PDF不存在: {full_pdf_path}")
            continue

        md_name = full_pdf_path.stem + ".md"
        md_path = EXTRACTED_DIR / md_name

        if md_path.exists() and md_path.stat().st_size > 100:
            skipped += 1
            continue

        logger.info(f"[{i+1}/{len(pending_reports)}] 预处理: {full_pdf_path.name}")
        text = preprocess_pdf(full_pdf_path)
        if text:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(text)
            processed += 1
            logger.info(f"  保存: {md_name} ({len(text)}字符)")
        else:
            logger.error(f"  预处理失败: {full_pdf_path.name}")

        if (i + 1) % 50 == 0:
            logger.info(f"预处理进度: {i+1}/{len(pending_reports)} 已处理:{processed} 跳过:{skipped}")

    logger.info(f"预处理完成: 新处理{processed}, 跳过{skipped}")
    return processed


# ========== 第2步：指标提取 ==========

def _filter_relevant_text(text, dimension, keep_ratio=0.3):
    dim_keywords = {
        "E": ["排放", "碳", "能源", "环境", "水", "废", "绿", "气候",
              "ISO14001", "生物", "光伏", "风电", "清洁"],
        "S": ["员工", "培训", "安全", "性别", "女性", "劳动", "公益",
              "慈善", "研发", "供应链", "质量", "产品安全", "数据安全",
              "隐私", "社区", "健康", "多元化"],
        "G": ["董事会", "董事", "独立董事", "监事", "ESG治理", "可持续发展委员会",
              "反腐", "合规", "风险", "内控", "商业道德", "投资者关系",
              "股东", "利益相关", "信息披露", "透明度"],
    }
    keywords = dim_keywords.get(dimension, [])
    paragraphs = text.split("\n")
    scored = []
    for para in paragraphs:
        if len(para.strip()) < 10:
            continue
        score = sum(1 for kw in keywords if kw in para)
        if score > 0:
            scored.append((score, para))
    if not scored:
        return ""
    scored.sort(key=lambda x: -x[0])
    keep_count = max(min(int(len(paragraphs) * keep_ratio), len(scored)), len(scored))
    return "\n".join(para for _, para in scored[:keep_count])


def _chunk_text(text):
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + CHUNK_SIZE
        if end >= text_len:
            chunks.append(text[start:])
            break
        chunk = text[start:end]
        last_nl = max(
            chunk.rfind("\n\n"), chunk.rfind("\n"),
            chunk.rfind("。"), chunk.rfind("."),
        )
        if last_nl > CHUNK_SIZE * 0.5:
            end = start + last_nl + 1
            chunks.append(text[start:end])
            start = end - CHUNK_OVERLAP
        else:
            chunks.append(chunk)
            start = end - CHUNK_OVERLAP
    return chunks


def _deduplicate(items):
    seen = {}
    for item in items:
        ind_id = item.get("id", "")
        if not ind_id:
            continue
        if ind_id not in seen or (
            item.get("confidence") == "high"
            and seen[ind_id].get("confidence") != "high"
        ):
            seen[ind_id] = item
    return list(seen.values())


def run_extract(pending_reports, limit=None):
    """对新预处理的MD文件调用DeepSeek API提取指标"""
    logger.info(f"=== 第2步：指标提取 ({len(pending_reports)}个) ===")

    # 收集需要提取的MD文件（没有对应result JSON的）
    to_extract = []
    for rep in pending_reports:
        pdf_path = rep.get("pdf_path", "")
        if not pdf_path:
            continue
        md_name = Path(pdf_path).stem + ".md"
        md_path = EXTRACTED_DIR / md_name
        result_name = Path(pdf_path).stem + "_result.json"
        result_path = OUTPUT_DIR / result_name

        if result_path.exists():
            continue  # 已有结果，跳过
        if md_path.exists():
            to_extract.append({
                "md_path": md_path,
                "company_name": rep["name"],
                "year": str(rep["year"]),
                "report_id": rep["report_id"],
            })

    if limit:
        to_extract = to_extract[:limit]

    logger.info(f"需提取: {len(to_extract)}个 (跳过{len(pending_reports) - len(to_extract)}个已有结果)")

    if not DEEPSEEK_API_KEY:
        logger.error("未设置DEEPSEEK_API_KEY")
        return 0

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    # 导入指标定义和提示词
    from src.extractor.indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION
    from src.extractor.prompts import (
        build_system_prompt, build_dimension_prompt,
        FEW_SHOT_EXAMPLE_QUANTITATIVE, FEW_SHOT_EXAMPLE_QUALITATIVE,
    )
    from src.extractor.validator import ESGValidator

    system_prompt = build_system_prompt()
    extracted = 0

    for i, item in enumerate(to_extract):
        if not cost_tracker.can_continue():
            logger.warning("预算不足，停止提取")
            break

        md_path = item["md_path"]
        company_name = item["company_name"]
        year = item["year"]

        logger.info(f"[{i+1}/{len(to_extract)}] {company_name} ({year})")
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                report_text = f.read()
        except Exception as e:
            logger.error(f"读取MD失败: {e}")
            continue

        if not report_text.strip():
            logger.warning(f"文本为空: {md_path.name}")
            continue

        all_results = {
            "company_name": company_name,
            "report_year": year,
            "quantitative_indicators": [],
            "qualitative_indicators": [],
        }

        for dim in ["E", "S", "G"]:
            dim_text = _filter_relevant_text(report_text, dim)
            if not dim_text:
                continue

            chunks = _chunk_text(dim_text)
            for ci, chunk in enumerate(chunks):
                if not cost_tracker.can_continue():
                    break

                prompt_template = build_dimension_prompt(dim)
                prompt = prompt_template.replace("{report_chunk}", chunk)

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": FEW_SHOT_EXAMPLE_QUANTITATIVE},
                    {"role": "assistant", "content": '{"quantitative_indicators": [], "qualitative_indicators": []}'},
                    {"role": "user", "content": FEW_SHOT_EXAMPLE_QUALITATIVE},
                    {"role": "assistant", "content": '{"quantitative_indicators": [], "qualitative_indicators": []}'},
                    {"role": "user", "content": prompt},
                ]

                try:
                    response = client.chat.completions.create(
                        model=DEEPSEEK_MODEL,
                        messages=messages,
                        temperature=0.1,
                        max_tokens=4096,
                        response_format={"type": "json_object"},
                    )
                except Exception as e:
                    logger.error(f"API调用失败: {e}")
                    cost_tracker.record_error()
                    time.sleep(2)
                    continue

                usage = response.usage
                cost_tracker.record(
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                )

                content = response.choices[0].message.content
                content = re.sub(r"^```(?:json)?\s*", "", content.strip())
                content = re.sub(r"\s*```$", "", content)

                try:
                    chunk_result = json.loads(content)
                    for qt in chunk_result.get("quantitative_indicators", []):
                        all_results["quantitative_indicators"].append(qt)
                    for ql in chunk_result.get("qualitative_indicators", []):
                        all_results["qualitative_indicators"].append(ql)
                except json.JSONDecodeError:
                    logger.warning(f"JSON解析失败: {content[:200]}")

                time.sleep(0.5)

            if not cost_tracker.can_continue():
                break

        # 去重
        all_results["quantitative_indicators"] = _deduplicate(all_results["quantitative_indicators"])
        all_results["qualitative_indicators"] = _deduplicate(all_results["qualitative_indicators"])

        # 校验
        validator = ESGValidator()
        validation = validator.validate(all_results)
        completeness = validator.check_completeness(all_results)
        all_results["validation"] = validation
        all_results["completeness"] = completeness

        # 保存
        result_path = OUTPUT_DIR / f"{md_path.stem}_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        logger.info(
            f"  质量分: {validation['overall_quality_score']:.2f} | "
            f"覆盖度: {completeness['completeness']}% | "
            f"定量: {validation['quantitative_valid']}/{validation['quantitative_count']} | "
            f"定性: {validation['qualitative_valid']}/{validation['qualitative_count']}"
        )
        extracted += 1

        if (i + 1) % 20 == 0:
            logger.info(f"费用: {cost_tracker.summary()}")

    logger.info(f"提取完成: {extracted}个, {cost_tracker.summary()}")
    return extracted


# ========== 第3步：导入数据库 ==========

def run_db_import():
    """将output目录下的结果JSON导入数据库"""
    logger.info("=== 第3步：导入数据库 ===")
    from src.utils.db import Database, import_results_from_json

    db = Database()
    stats = import_results_from_json(db)
    logger.info(f"导入: 公司{stats['companies']}, 报告{stats['reports']}, 定量{stats['values']}, 定性{stats['texts']}")
    if stats.get("errors"):
        for e in stats["errors"][:5]:
            logger.warning(f"  {e}")
    return stats


# ========== 主流程 ==========

def main():
    # 获取待处理报告
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id AS report_id, r.year, r.pdf_path, r.extraction_status,
               c.stock_code, c.name
        FROM reports r
        JOIN companies c ON r.company_id = c.id
        WHERE r.extraction_status = 'pending' OR r.extraction_status IS NULL
        ORDER BY c.stock_code
    """)
    pending = [dict(row) for row in cursor.fetchall()]
    conn.close()

    logger.info(f"待处理报告: {len(pending)}")

    if not pending:
        logger.info("没有待处理的报告")
        return

    # 第1步：预处理
    processed = run_preprocess(pending)
    logger.info(f"第1步完成: 预处理了{processed}个PDF")

    # 第2步：提取
    extracted = run_extract(pending)
    logger.info(f"第2步完成: 提取了{extracted}个报告")

    # 第3步：导入
    if extracted > 0:
        stats = run_db_import()
        logger.info(f"第3步完成: {stats}")

    logger.info("=== 流水线完成 ===")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", choices=["preprocess", "extract", "import", "all"], default="all")
    parser.add_argument("--limit", type=int, default=None, help="限制提取数量")
    args = parser.parse_args()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id AS report_id, r.year, r.pdf_path, r.extraction_status,
               c.stock_code, c.name
        FROM reports r
        JOIN companies c ON r.company_id = c.id
        WHERE r.extraction_status = 'pending' OR r.extraction_status IS NULL
        ORDER BY c.stock_code
    """)
    pending = [dict(row) for row in cursor.fetchall()]
    conn.close()

    logger.info(f"待处理报告: {len(pending)}")

    if args.step in ("preprocess", "all"):
        run_preprocess(pending)
    if args.step in ("extract", "all"):
        run_extract(pending, limit=args.limit)
    if args.step in ("import", "all"):
        run_db_import()
