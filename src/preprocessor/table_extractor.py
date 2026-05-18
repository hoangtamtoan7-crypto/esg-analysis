"""表格提取器

使用pdfplumber和camelot提取PDF中的表格数据。
ESG报告中经常包含关键数据表格（排放数据、能耗统计等）。
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"


class TableExtractor:
    """PDF表格提取器"""

    def extract_with_pdfplumber(self, pdf_path: Path) -> List[dict]:
        """使用pdfplumber提取表格（适合规则表格）"""
        import pdfplumber

        tables = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    extracted = page.extract_tables()
                    for t_idx, table in enumerate(extracted):
                        if not table or len(table) < 2:
                            continue

                        # 清洗数据
                        clean_table = []
                        for row in table:
                            clean_row = [
                                str(c).strip().replace("\n", " ") if c else ""
                                for c in row
                            ]
                            clean_table.append(clean_row)

                        # 过滤无效表格（全是空或单列）
                        non_empty = sum(
                            1 for row in clean_table if any(cell for cell in row)
                        )
                        if non_empty < 2:
                            continue

                        tables.append({
                            "page": page_num + 1,
                            "index": t_idx,
                            "rows": len(clean_table),
                            "cols": len(clean_table[0]) if clean_table else 0,
                            "headers": clean_table[0] if clean_table else [],
                            "data": clean_table[1:],
                        })

        except Exception as e:
            logger.error(f"pdfplumber表格提取失败 {pdf_path.name}: {e}")

        return tables

    def extract_with_camelot(self, pdf_path: Path) -> List[dict]:
        """使用camelot提取表格（适合更复杂的表格）"""
        tables = []
        try:
            import camelot

            # stream模式（适合有空白分隔的表格）
            extracted = camelot.read_pdf(
                str(pdf_path), pages="all", flavor="stream",
                edge_tol=50, row_tol=10,
            )

            for i, table in enumerate(extracted):
                df = table.df
                if df.shape[0] < 2:
                    continue

                tables.append({
                    "page": table.page,
                    "index": i,
                    "rows": df.shape[0],
                    "cols": df.shape[1],
                    "headers": df.iloc[0].tolist(),
                    "data": df.iloc[1:].values.tolist(),
                    "accuracy": float(table.parsing_report.get("accuracy", 0)),
                })

            logger.info(f"camelot从{pdf_path.name}提取{len(tables)}个表格")

        except ImportError:
            logger.debug("camelot未安装，跳过")
        except Exception as e:
            logger.debug(f"camelot提取失败 {pdf_path.name}: {e}")

        return tables

    def extract_all(self, pdf_path: Path) -> List[dict]:
        """综合两种方法提取表格，合并去重"""
        # 优先使用pdfplumber（更快）
        tables = self.extract_with_pdfplumber(pdf_path)

        # camelot作为补充
        if len(tables) < 3:
            try:
                camelot_tables = self.extract_with_camelot(pdf_path)
                # 简单去重：同一页的表格如数量相同则跳过
                existing_pages = {t["page"] for t in tables}
                for ct in camelot_tables:
                    if ct["page"] not in existing_pages:
                        tables.append(ct)
            except Exception:
                pass

        # 按页码排序
        tables.sort(key=lambda t: (t["page"], t["index"]))
        return tables

    def find_esg_data_tables(self, tables: List[dict]) -> List[dict]:
        """筛选包含ESG关键数据的表格"""
        esg_keywords = [
            "排放", "碳", "能源", "水", "废", "员工", "培训",
            "安全", "薪酬", "董事", "环境", "治理", "温室气体",
            "GHG", "CO2", "NOx", "SOx", "MWh", "ESG",
        ]

        esg_tables = []
        for table in tables:
            all_text = " ".join(table.get("headers", []))
            for row in (table.get("data", []) or []):
                all_text += " " + " ".join(str(c) for c in row)

            score = sum(1 for kw in esg_keywords if kw.lower() in all_text.lower())
            if score > 0:
                table["esg_keyword_score"] = score
                esg_tables.append(table)

        return esg_tables

    def tables_to_markdown(self, tables: List[dict]) -> str:
        """将提取的表格转换为Markdown文本，方便大模型理解"""
        md_parts = []
        for i, table in enumerate(tables):
            md_parts.append(f"\n### 表格 {i+1} (第{table['page']}页)\n")

            headers = table.get("headers", [])
            data = table.get("data", [])

            # 表头
            md_parts.append("| " + " | ".join(str(h) for h in headers) + " |")
            md_parts.append("| " + " | ".join(["---"] * len(headers)) + " |")

            # 数据行
            for row in data:
                cells = [str(c).replace("\n", " ") for c in row]
                # 补齐列数
                while len(cells) < len(headers):
                    cells.append("")
                md_parts.append("| " + " | ".join(cells[:len(headers)]) + " |")

        return "\n".join(md_parts)

    def process_and_save(self, pdf_path: Path) -> Path:
        """提取表格并保存为JSON"""
        tables = self.extract_all(pdf_path)
        esg_tables = self.find_esg_data_tables(tables)

        output_path = EXTRACTED_DIR / f"{pdf_path.stem}_tables.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(esg_tables, f, ensure_ascii=False, indent=2)

        # 同时保存Markdown版本（方便大模型使用）
        if esg_tables:
            md_output = EXTRACTED_DIR / f"{pdf_path.stem}_tables.md"
            md_text = self.tables_to_markdown(esg_tables)
            with open(md_output, "w", encoding="utf-8") as f:
                f.write(md_text)

        logger.info(
            f"表格提取: {pdf_path.name} -> {len(esg_tables)}个ESG相关表格"
        )
        return output_path


if __name__ == "__main__":
    extractor = TableExtractor()
    pdf_dir = BASE_DIR / "data" / "pdfs"
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if pdfs:
        for pdf in pdfs[:3]:  # 测试前3个
            extractor.process_and_save(pdf)
