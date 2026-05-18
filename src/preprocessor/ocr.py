"""OCR识别模块

使用PaddleOCR识别PDF中嵌入图片的文字（处理扫描件、图表内嵌文字等）。
"""

import logging
import os
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"


class OCRProcessor:
    """OCR处理器，用于识别PDF截图/扫描件中的文字"""

    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        """延迟加载PaddleOCR"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    use_gpu=False,
                    show_log=False,
                )
                logger.info("PaddleOCR初始化成功")
            except ImportError:
                logger.warning("PaddleOCR未安装，OCR功能不可用")
                logger.warning("安装命令: pip install paddlepaddle paddleocr")
                self._ocr = False
            except Exception as e:
                logger.error(f"PaddleOCR初始化失败: {e}")
                self._ocr = False
        return self._ocr

    def extract_text_from_image(self, image_path: str) -> str:
        """从图片中提取文字

        Args:
            image_path: 图片文件路径

        Returns:
            识别出的文字
        """
        if not self.ocr:
            return ""

        try:
            result = self.ocr.ocr(image_path, cls=True)
            if not result or not result[0]:
                return ""

            lines = []
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                if confidence > 0.7:  # 只保留置信度>70%的结果
                    lines.append(text)

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"OCR识别失败 {image_path}: {e}")
            return ""

    def extract_texts_from_pdf_images(self, pdf_path: Path) -> str:
        """从PDF中提取所有图片并用OCR识别

        适用于扫描件PDF或含有图片表格的PDF。

        Returns:
            所有OCR识别文字拼接
        """
        import fitz  # PyMuPDF

        all_text = []
        try:
            doc = fitz.open(str(pdf_path))
            logger.info(f"OCR处理: {pdf_path.name} ({len(doc)}页)")

            for page_num, page in enumerate(doc):
                # 先尝试普通文本提取
                text = page.get_text()
                if len(text.strip()) > 100:
                    # 该页文本充足，跳过OCR
                    continue

                # 文本不足的页可能是扫描件，转为图片再OCR
                pix = page.get_pixmap(dpi=200)
                img_path = str(EXTRACTED_DIR / f"_ocr_temp_{pdf_path.stem}_p{page_num}.png")
                pix.save(img_path)

                ocr_text = self.extract_text_from_image(img_path)
                if ocr_text:
                    all_text.append(f"--- OCR 第{page_num+1}页 ---\n{ocr_text}")

                # 清理临时文件
                if os.path.exists(img_path):
                    os.remove(img_path)

            doc.close()
        except Exception as e:
            logger.error(f"OCR处理失败 {pdf_path.name}: {e}")

        return "\n\n".join(all_text)

    def is_scanned_pdf(self, pdf_path: Path, threshold: float = 0.3) -> bool:
        """判断PDF是否为扫描件

        Args:
            pdf_path: PDF路径
            threshold: 文本页面比例阈值，低于此比例认为是扫描件

        Returns:
            True=扫描件, False=普通可提取文本的PDF
        """
        import fitz

        try:
            doc = fitz.open(str(pdf_path))
            text_pages = 0
            total_pages = min(len(doc), 10)  # 检查前10页

            for i in range(total_pages):
                text = doc[i].get_text()
                if len(text.strip()) > 100:
                    text_pages += 1

            doc.close()

            text_ratio = text_pages / max(total_pages, 1)
            return text_ratio < threshold
        except Exception:
            return False


if __name__ == "__main__":
    ocr = OCRProcessor()
    # 测试：检查第一个PDF是否为扫描件
    pdf_dir = BASE_DIR / "data" / "pdfs"
    pdfs = list(pdf_dir.glob("*.pdf"))
    if pdfs:
        is_scanned = ocr.is_scanned_pdf(pdfs[0])
        print(f"{pdfs[0].name}: 扫描件={'是' if is_scanned else '否'}")
