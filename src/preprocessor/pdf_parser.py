"""PDF文本提取器

使用pdfplumber提取PDF中的文本、表格，将ESG报告转换为结构化文本。
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 项目路径
BASE_DIR = Path(__file__).parent.parent.parent
PDF_DIR = BASE_DIR / "data" / "pdfs"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"


class PDFParser:
    """ESG报告PDF解析器"""

    def __init__(self):
        EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    def extract_text(self, pdf_path: Path) -> str:
        """提取PDF全文文本

        Args:
            pdf_path: PDF文件路径

        Returns:
            提取的完整文本
        """
        import pdfplumber

        all_text = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                logger.info(f"解析PDF: {pdf_path.name} ({len(pdf.pages)}页)")
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        all_text.append(f"--- 第{i+1}页 ---\n{text}")
        except Exception as e:
            logger.error(f"pdfplumber提取失败 {pdf_path.name}: {e}")
            # 回退到PyMuPDF
            return self._extract_text_fallback(pdf_path)

        return "\n\n".join(all_text)

    def _extract_text_fallback(self, pdf_path: Path) -> str:
        """使用PyMuPDF作为备选提取方案"""
        import fitz

        all_text = []
        try:
            doc = fitz.open(str(pdf_path))
            logger.info(f"使用PyMuPDF备选方案: {pdf_path.name} ({len(doc)}页)")
            for i, page in enumerate(doc):
                text = page.get_text()
                if text:
                    all_text.append(f"--- 第{i+1}页 ---\n{text}")
            doc.close()
        except Exception as e:
            logger.error(f"PyMuPDF也提取失败 {pdf_path.name}: {e}")
            return ""

        return "\n\n".join(all_text)

    def extract_tables(self, pdf_path: Path) -> List[dict]:
        """提取PDF中的表格

        Returns:
            [{page, index, headers, rows}, ...]
        """
        import pdfplumber

        tables = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    extracted = page.extract_tables()
                    for idx, table in enumerate(extracted):
                        if table and len(table) > 1:
                            # 第一行作为表头
                            headers = [
                                str(cell).strip() if cell else ""
                                for cell in table[0]
                            ]
                            rows = []
                            for row in table[1:]:
                                cells = [
                                    str(cell).strip() if cell else ""
                                    for cell in row
                                ]
                                if any(cells):  # 跳过全空行
                                    rows.append(cells)
                            if rows:
                                tables.append({
                                    "page": page_num + 1,
                                    "table_index": idx,
                                    "headers": headers,
                                    "rows": rows,
                                })
        except Exception as e:
            logger.error(f"表格提取失败 {pdf_path.name}: {e}")

        return tables

    def extract_text_with_tables(self, pdf_path: Path) -> str:
        """提取文本并将表格格式化为Markdown表格嵌入"""
        import pdfplumber

        parts = []
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for i, page in enumerate(pdf.pages):
                    parts.append(f"--- 第{i+1}页 ---")

                    # 提取表格
                    tables = page.extract_tables()
                    has_tables = bool(tables and any(len(t) > 1 for t in tables))

                    # 提取文本
                    text = page.extract_text()
                    if text:
                        parts.append(text)

                    # 格式化表格
                    if has_tables:
                        for t_idx, table in enumerate(tables):
                            if not table or len(table) < 2:
                                continue
                            md_table = self._table_to_markdown(table)
                            if md_table:
                                parts.append(f"\n[表格 {t_idx+1}]\n{md_table}")

        except Exception as e:
            logger.error(f"提取失败 {pdf_path.name}: {e}")
            return self._extract_text_fallback(pdf_path)

        return "\n\n".join(parts)

    def _table_to_markdown(self, table: list) -> str:
        """将表格转换为Markdown格式"""
        if not table or len(table) < 2:
            return ""

        # 清理单元格内容
        clean_table = []
        for row in table:
            clean_row = [str(c).strip().replace("\n", " ") if c else "" for c in row]
            clean_table.append(clean_row)

        # 生成Markdown
        lines = []
        # 表头
        header = clean_table[0]
        lines.append("| " + " | ".join(h for h in header if h) + " |")
        # 分隔行
        lines.append("|" + "|".join(["---" for _ in header]) + "|")
        # 数据行
        for row in clean_table[1:]:
            if any(cell for cell in row):
                lines.append("| " + " | ".join(cell for cell in row) + " |")

        return "\n".join(lines)

    def parse_and_save(self, pdf_path: Path, output_format: str = "both") -> dict:
        """解析PDF并保存结果

        Args:
            pdf_path: PDF路径
            output_format: "text" / "tables" / "both"

        Returns:
            {"text_path": ..., "tables_path": ..., "page_count": ...}
        """
        result = {"page_count": 0, "text_path": None, "tables_path": None}

        base_name = pdf_path.stem

        if output_format in ("text", "both"):
            text = self.extract_text_with_tables(pdf_path)
            text_path = EXTRACTED_DIR / f"{base_name}.md"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(text)
            result["text_path"] = str(text_path)
            logger.info(f"文本已保存: {text_path} ({len(text)}字符)")

        if output_format in ("tables", "both"):
            tables = self.extract_tables(pdf_path)
            tables_path = EXTRACTED_DIR / f"{base_name}_tables.json"
            with open(tables_path, "w", encoding="utf-8") as f:
                json.dump(tables, f, ensure_ascii=False, indent=2)
            result["tables_path"] = str(tables_path)
            result["table_count"] = len(tables)
            logger.info(f"表格已保存: {tables_path} ({len(tables)}个表格)")

        return result

    def batch_parse(self, limit: Optional[int] = None, skip_existing: bool = True,
                    company_codes: Optional[set] = None) -> List[dict]:
        """批量解析PDF目录中的所有文件"""
        pdf_files = sorted(PDF_DIR.glob("*.pdf"))
        if company_codes:
            pdf_files = [f for f in pdf_files if f.stem.split("_")[0] in company_codes]
        if limit:
            pdf_files = pdf_files[:limit]

        results = []
        for i, pdf_path in enumerate(pdf_files):
            base_name = pdf_path.stem
            text_path = EXTRACTED_DIR / f"{base_name}.md"
            tables_path = EXTRACTED_DIR / f"{base_name}_tables.json"

            if skip_existing and text_path.exists() and tables_path.exists():
                logger.info(f"[{i+1}/{len(pdf_files)}] 跳过(已存在): {pdf_path.name}")
                results.append({"filename": pdf_path.name, "skipped": True})
                continue

            logger.info(f"[{i+1}/{len(pdf_files)}] 处理: {pdf_path.name}")
            try:
                result = self.parse_and_save(pdf_path)
                result["filename"] = pdf_path.name
                results.append(result)
            except Exception as e:
                logger.error(f"处理失败 {pdf_path.name}: {e}")
                results.append({"filename": pdf_path.name, "error": str(e)})

        return results


if __name__ == "__main__":
    parser = PDFParser()
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    if pdf_files:
        # 测试第一个PDF
        result = parser.parse_and_save(pdf_files[0])
        print(f"解析完成: {result}")
    else:
        print("PDF目录为空，请先运行下载器")
