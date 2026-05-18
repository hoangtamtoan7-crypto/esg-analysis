"""ESG指标提取引擎

使用DeepSeek API从ESG报告中提取定量和定性指标。
采用分层策略：先按维度分块提取，再聚合校验。
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

from openai import OpenAI

from .config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, cost_tracker,
    EXTRACTED_DIR, OUTPUT_DIR,
)
from .indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION, get_indicator_by_id
from .prompts import (
    build_system_prompt, build_dimension_prompt, build_keyword_match_prompt,
    FEW_SHOT_EXAMPLE_QUANTITATIVE, FEW_SHOT_EXAMPLE_QUALITATIVE,
)
from .validator import ESGValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 分块大小（字符数）
CHUNK_SIZE = 8000
CHUNK_OVERLAP = 500

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ESGExtractor:
    """ESG报告指标提取器"""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or DEEPSEEK_API_KEY
        if not key:
            raise ValueError("请设置DEEPSEEK_API_KEY环境变量或传入api_key参数")

        self.client = OpenAI(api_key=key, base_url=DEEPSEEK_BASE_URL)
        self.system_prompt = build_system_prompt()

    def extract_from_text(self, report_text: str, company_name: str = "",
                          report_year: str = "", dimension: Optional[str] = None) -> dict:
        """从报告文本中提取ESG指标

        Args:
            report_text: 报告全文
            company_name: 公司名称
            report_year: 报告年份
            dimension: 可选，仅提取E/S/G某一维度

        Returns:
            提取结果字典
        """
        if not report_text.strip():
            logger.warning("报告文本为空")
            return {"error": "empty_text"}

        # 确定提取维度
        if dimension and dimension in INDICATORS_BY_DIMENSION:
            dimensions = [dimension]
        else:
            dimensions = ["E", "S", "G"]

        all_results = {
            "company_name": company_name,
            "report_year": report_year,
            "quantitative_indicators": [],
            "qualitative_indicators": [],
        }

        for dim in dimensions:
            logger.info(f"提取维度: {dim}")
            dim_text = self._filter_relevant_text(report_text, dim)
            if not dim_text:
                logger.warning(f"维度{dim}无相关文本，跳过")
                continue

            chunks = self._chunk_text(dim_text)
            logger.info(f"维度{dim}: 文本{len(dim_text)}字符, 分为{len(chunks)}块")

            for i, chunk in enumerate(chunks):
                if not cost_tracker.can_continue():
                    logger.warning("预算不足，停止提取")
                    break

                try:
                    result = self._extract_chunk(chunk, dim, i, len(chunks))
                    if result:
                        for qt in result.get("quantitative_indicators", []):
                            all_results["quantitative_indicators"].append(qt)
                        for ql in result.get("qualitative_indicators", []):
                            all_results["qualitative_indicators"].append(ql)
                except Exception as e:
                    logger.error(f"提取失败 dim={dim} chunk={i}: {e}")
                    cost_tracker.record_error()

                time.sleep(0.3)  # 避免API限流

        # 去重合并
        all_results["quantitative_indicators"] = self._deduplicate(
            all_results["quantitative_indicators"], is_quantitative=True
        )
        all_results["qualitative_indicators"] = self._deduplicate(
            all_results["qualitative_indicators"], is_quantitative=False
        )

        return all_results

    def _extract_chunk(self, chunk: str, dimension: str,
                       chunk_idx: int = 0, total_chunks: int = 1) -> dict:
        """对单个文本块调用API提取指标"""
        # 减少每块提取的指标数量，按维度精准提取
        indicators = INDICATORS_BY_DIMENSION.get(dimension, [])
        prompt_template = build_dimension_prompt(dimension)
        prompt = prompt_template.replace("{report_chunk}", chunk)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": FEW_SHOT_EXAMPLE_QUANTITATIVE},
            {"role": "assistant", "content": '{"quantitative_indicators": [...]}'},
            {"role": "user", "content": FEW_SHOT_EXAMPLE_QUALITATIVE},
            {"role": "assistant", "content": '{"qualitative_indicators": [...]}'},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            cost_tracker.record_error()
            return {}

        usage = response.usage
        cost_tracker.record(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )

        content = response.choices[0].message.content
        logger.debug(
            f"chunk {chunk_idx+1}/{total_chunks}: "
            f"in={usage.prompt_tokens} out={usage.completion_tokens} "
            f"cost={cost_tracker.total_cost:.4f}元"
        )

        try:
            # 清理可能的Markdown代码块包裹
            content = re.sub(r"^```(?:json)?\s*", "", content.strip())
            content = re.sub(r"\s*```$", "", content)
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"JSON解析失败，返回原始内容: {content[:200]}")
            return {}

    def _filter_relevant_text(self, text: str, dimension: str, keep_ratio: float = 0.3) -> str:
        """用关键词过滤，保留与目标维度相关的文本段落

        这是减少token消耗的关键步骤 - 只保留最相关的段落
        """
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

        # 按相关度排序，保留top段落
        scored.sort(key=lambda x: -x[0])

        # 保留比例可调
        keep_count = max(min(int(len(paragraphs) * keep_ratio), len(scored)), len(scored))
        kept = [para for _, para in scored[:keep_count]]

        return "\n".join(kept)

    def _chunk_text(self, text: str) -> list:
        """将文本切分为适合API调用的块"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + CHUNK_SIZE
            if end >= text_len:
                chunks.append(text[start:])
                break

            # 尽量在段落边界切断
            chunk = text[start:end]
            # 找最后一个换行
            last_nl = max(
                chunk.rfind("\n\n"),
                chunk.rfind("\n"),
                chunk.rfind("。"),
                chunk.rfind("."),
            )
            if last_nl > CHUNK_SIZE * 0.5:
                end = start + last_nl + 1
                chunks.append(text[start:end])
                start = end - CHUNK_OVERLAP
            else:
                chunks.append(chunk)
                start = end - CHUNK_OVERLAP

        return chunks

    def _deduplicate(self, items: list, is_quantitative: bool) -> list:
        """去重合并多个chunk的提取结果"""
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

    def extract_from_file(self, md_path: Path, company_name: str = "",
                          report_year: str = "") -> dict:
        """从预处理后的Markdown文件提取指标"""
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()

        # 从文件名尝试提取公司和年份信息
        if not company_name:
            filename = md_path.stem
            parts = filename.split("_")
            if len(parts) >= 2:
                company_name = parts[1]
            if len(parts) >= 3:
                report_year = parts[2]

        return self.extract_from_text(text, company_name, report_year)

    def batch_extract(self, limit: Optional[int] = None) -> list:
        """批量处理所有预处理后的报告"""
        md_files = sorted(EXTRACTED_DIR.glob("*.md"))
        if limit:
            md_files = md_files[:limit]

        results = []
        for i, md_path in enumerate(md_files):
            logger.info(f"[{i+1}/{len(md_files)}] 提取: {md_path.name}")
            try:
                result = self.extract_from_file(md_path)
                result["source_file"] = md_path.name

                # 校验结果
                validator = ESGValidator()
                validation = validator.validate(result)
                completeness = validator.check_completeness(result)
                result["validation"] = validation
                result["completeness"] = completeness
                logger.info(
                    f"  质量分: {validation['overall_quality_score']:.2f} | "
                    f"覆盖度: {completeness['completeness']}% | "
                    f"有效定量: {validation['quantitative_valid']}/{validation['quantitative_count']} | "
                    f"有效定性: {validation['qualitative_valid']}/{validation['qualitative_count']}"
                )

                # 保存单个结果
                output_path = OUTPUT_DIR / f"{md_path.stem}_result.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                results.append(result)
            except Exception as e:
                logger.error(f"提取失败 {md_path.name}: {e}")

            logger.info(cost_tracker.summary())

        return results

    def get_cost_summary(self) -> str:
        return cost_tracker.summary()


def validate_existing(limit: Optional[int] = None) -> list:
    """对已有的提取结果JSON进行校验（不需要API调用）"""
    json_files = sorted(OUTPUT_DIR.glob("*_result.json"))
    if limit:
        json_files = json_files[:limit]

    validator = ESGValidator()
    validation_results = []

    for i, json_path in enumerate(json_files):
        logger.info(f"[{i+1}/{len(json_files)}] 校验: {json_path.name}")
        with open(json_path, "r", encoding="utf-8") as f:
            result = json.load(f)

        validation = validator.validate(result)
        completeness = validator.check_completeness(result)
        result["validation"] = validation
        result["completeness"] = completeness

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        validation_results.append({
            "file": json_path.name,
            "quality_score": validation["overall_quality_score"],
            "completeness": completeness["completeness"],
            "qt_valid": validation["quantitative_valid"],
            "qt_total": validation["quantitative_count"],
            "ql_valid": validation["qualitative_valid"],
            "ql_total": validation["qualitative_count"],
        })
        logger.info(
            f"  质量分: {validation['overall_quality_score']:.2f} | "
            f"覆盖度: {completeness['completeness']}%"
        )

    # 汇总报告
    if validation_results:
        scores = [v["quality_score"] for v in validation_results]
        comps = [v["completeness"] for v in validation_results]
        logger.info(
            f"\n校验汇总: {len(validation_results)}个报告 | "
            f"平均质量分: {sum(scores)/len(scores):.2f} | "
            f"平均覆盖度: {sum(comps)/len(comps):.1f}%"
        )

    return validation_results


if __name__ == "__main__":
    # 测试：从第一个markdown文件提取
    md_files = sorted(EXTRACTED_DIR.glob("*.md"))
    if not md_files:
        logger.warning("请先运行预处理器生成markdown文件")
    else:
        api_key = os.getenv("DEEPSEEK_API_KEY") or input("请输入DeepSeek API Key: ")
        extractor = ESGExtractor(api_key=api_key)
        result = extractor.extract_from_file(md_files[0])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(extractor.get_cost_summary())
