"""ESG报告下载器

从巨潮资讯网等数据源下载上市公司ESG报告PDF。
"""

import csv
import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Origin": "http://www.cninfo.com.cn",
    "Referer": "http://www.cninfo.com.cn/new/index",
}

BASE_DIR = Path(__file__).parent.parent.parent
COMPANY_LIST_PATH = BASE_DIR / "data" / "company_list.csv"
PDF_DIR = BASE_DIR / "data" / "pdfs"
DOWNLOAD_LOG_PATH = BASE_DIR / "data" / "download_log.csv"

# 需要跳过的标题关键词
SKIP_TITLE_KEYWORDS = ["英文版", "摘要", "目录", "修订"]

# 搜索关键词按命中率排序（优先用最可能命中的词做快速检查）
ESG_KEYWORDS_FAST = ["ESG报告", "可持续发展报告", "社会责任报告"]
ESG_KEYWORDS_REST = [
    "环境、社会及管治报告", "环境、社会与管治报告",
    "企业社会责任报告", "ESG Report", "Sustainability Report", "CSR报告",
]

SAVE_INTERVAL = 50  # 每处理50家公司保存一次日志


def _clean_title(title: str) -> str:
    """去除HTML标签"""
    return re.sub(r"<[^>]+>", "", title)


def _sanitize_filename(name: str) -> str:
    """清理公司名中的非法文件名字符"""
    # Windows 非法字符: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # 全角字符转半角
    name = name.replace('Ａ', 'A').replace('Ｂ', 'B').replace('Ｃ', 'C')
    # 多余空格
    name = re.sub(r'\s+', '', name)
    return name


class ESGReportDownloader:
    """ESG报告下载器（支持断点续传）"""

    def __init__(self, resume: bool = True):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        self.download_log = []
        self.processed_codes = set()
        if resume:
            self._load_existing_log()
        self._init_session()

    def _load_existing_log(self):
        """加载已有下载日志，实现断点续传（只跳过已成功下载的）"""
        if not DOWNLOAD_LOG_PATH.exists():
            return
        try:
            with open(DOWNLOAD_LOG_PATH, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    code = row.get("code", "")
                    status = row.get("status", "")
                    if code:
                        self.download_log.append(row)
                        if status == "success":
                            self.processed_codes.add(code)
            logger.info(f"断点续传: 已加载 {len(self.download_log)} 条记录，跳过 {len(self.processed_codes)} 家已成功")
        except Exception:
            pass

    def _init_session(self):
        """初始化会话，获取cookie"""
        try:
            self.session.get(
                "http://www.cninfo.com.cn/new/index", timeout=15
            )
        except Exception:
            pass

    def search(self, stock_code: str, keyword: str, page_size: int = 30) -> list:
        """在巨潮资讯网全文搜索公告"""
        url = "http://www.cninfo.com.cn/new/fulltextSearch/full"
        params = {
            "searchkey": f"{keyword} {stock_code}",
            "pageNum": 1,
            "pageSize": page_size,
            "sortName": "pubdate",
            "sortType": "desc",
        }
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("announcements") or []
        except Exception as e:
            logger.warning(f"搜索失败 {stock_code} {keyword}: {e}")
            return []

    def _build_pdf_url(self, adjunct_url: str) -> str:
        """构造PDF下载URL"""
        if not adjunct_url:
            return ""
        if adjunct_url.startswith("http"):
            return adjunct_url
        return f"http://static.cninfo.com.cn/{adjunct_url}"

    def _is_valid_announcement(self, ann: dict) -> bool:
        """检查公告是否为有效的ESG报告"""
        title = _clean_title(ann.get("announcementTitle", ""))
        adjunct_url = ann.get("adjunctUrl", "")

        # 必须是PDF
        if not adjunct_url.lower().endswith(".pdf"):
            return False
        # 跳过不需要的版本
        if any(kw in title for kw in SKIP_TITLE_KEYWORDS):
            return False
        return True

    def download_pdf(self, url: str, filepath: Path, stock_code: str = "") -> bool:
        """下载PDF并验证。如果已有同代码的PDF则跳过"""
        # 检查是否已有同股票代码的PDF（处理文件名清理前后的差异）
        existing = list(filepath.parent.glob(f"{stock_code}_*.pdf")) if stock_code else []
        if existing:
            existing_path = existing[0]
            if existing_path.stat().st_size > 10_000:
                logger.info(f"已存在，跳过: {existing_path.name}")
                return True

        try:
            resp = self.session.get(url, timeout=60, stream=True)
            resp.raise_for_status()

            # 验证是否为PDF
            first_bytes = next(resp.iter_content(chunk_size=10), b"")
            if b"%PDF" not in first_bytes:
                logger.warning(f"非PDF内容: {url[:80]}")
                return False

            with open(filepath, "wb") as f:
                f.write(first_bytes)
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"下载成功: {filepath.name} ({filepath.stat().st_size / 1024:.0f} KB)")
            return True

        except Exception as e:
            logger.error(f"下载失败 {url[:80]}: {e}")
            if filepath.exists():
                filepath.unlink()
            return False

    def find_and_download(
        self, stock_code: str, company_name: str, year: str = "2025"
    ) -> Optional[Path]:
        """为一家公司搜索并下载最新的ESG报告"""
        # 收集所有搜索到的公告
        all_announcements = []
        seen_ids = set()

        # 先用高命中率关键词快速搜索
        for keyword in ESG_KEYWORDS_FAST:
            announcements = self.search(stock_code, keyword)
            for ann in announcements:
                aid = ann.get("announcementId", "")
                if aid and aid not in seen_ids:
                    seen_ids.add(aid)
                    all_announcements.append(ann)
            time.sleep(0.3)

        # 如果快速关键词没找到，尝试其他关键词
        if not all_announcements:
            for keyword in ESG_KEYWORDS_REST:
                announcements = self.search(stock_code, keyword)
                for ann in announcements:
                    aid = ann.get("announcementId", "")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        all_announcements.append(ann)
                time.sleep(0.3)

        if not all_announcements:
            self.download_log.append({
                "code": stock_code, "name": company_name,
                "title": "", "year": "", "status": "no_esg_report",
            })
            return None

        # 过滤有效公告，按时间排序
        valid = [
            ann for ann in all_announcements
            if self._is_valid_announcement(ann)
        ]
        # 优先选非英文的完整版报告
        valid.sort(
            key=lambda a: (
                "英文" in _clean_title(a.get("announcementTitle", "")),
                -(a.get("announcementTime", 0) or 0),
            )
        )

        if not valid:
            logger.warning(f"无有效PDF: {stock_code} {company_name}")
            self.download_log.append({
                "code": stock_code, "name": company_name,
                "title": "", "year": "", "status": "no_valid_pdf",
            })
            return None

        # 下载最佳匹配
        best = valid[0]
        title = _clean_title(best.get("announcementTitle", ""))
        adjunct_url = best.get("adjunctUrl", "")
        pdf_url = self._build_pdf_url(adjunct_url)

        # 从标题或时间戳提取年份
        ts = best.get("announcementTime", 0)
        if ts:
            from datetime import datetime
            year = datetime.fromtimestamp(ts / 1000).strftime("%Y")

        safe_name = _sanitize_filename(company_name)
        filename = f"{stock_code}_{safe_name}_{year}.pdf"
        filepath = PDF_DIR / filename

        logger.info(f"下载: {company_name} — {title[:50]}")
        if self.download_pdf(pdf_url, filepath, stock_code):
            self.download_log.append({
                "code": stock_code, "name": company_name,
                "title": title, "year": year,
                "filepath": str(filepath), "status": "success",
            })
            return filepath

        self.download_log.append({
            "code": stock_code, "name": company_name,
            "title": title, "year": year, "status": "download_failed",
        })
        return None

    def run(self, limit: Optional[int] = None, delay: float = 1.0):
        """批量下载ESG报告（支持断点续传）"""
        companies = self._load_company_list()

        # 过滤已处理的公司
        new_companies = [
            c for c in companies if c["code"] not in self.processed_codes
        ]
        skipped = len(companies) - len(new_companies)
        if skipped:
            logger.info(f"断点续传: 跳过 {skipped} 家已处理公司，剩余 {len(new_companies)} 家")

        if limit:
            new_companies = new_companies[:limit]

        logger.info(f"开始下载 {len(new_companies)} 家公司的ESG报告...")
        success_count = 0
        fail_count = 0
        no_esg_count = 0

        for i, row in enumerate(tqdm(new_companies, desc="下载ESG报告")):
            code = row["code"]
            name = row["name"]
            result = self.find_and_download(code, name)
            if result:
                success_count += 1
            elif self.download_log and self.download_log[-1].get("status") == "no_esg_report":
                no_esg_count += 1
            else:
                fail_count += 1
            time.sleep(delay)

            # 定期保存日志
            if (i + 1) % SAVE_INTERVAL == 0:
                self._save_log()
                logger.info(
                    f"进度: {i+1}/{len(new_companies)} "
                    f"成功:{success_count} 无报告:{no_esg_count} 失败:{fail_count}"
                )

        self._save_log()
        logger.info(
            f"下载完成！成功: {success_count}, 无ESG报告: {no_esg_count}, 失败: {fail_count}"
        )

    def _load_company_list(self) -> list:
        companies = []
        with open(COMPANY_LIST_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                companies.append(row)
        return companies

    def _save_log(self):
        with open(DOWNLOAD_LOG_PATH, "w", newline="", encoding="utf-8") as f:
            if not self.download_log:
                return
            writer = csv.DictWriter(f, fieldnames=self.download_log[0].keys())
            writer.writeheader()
            writer.writerows(self.download_log)


if __name__ == "__main__":
    downloader = ESGReportDownloader()
    # 先试下载前5家公司做测试
    downloader.run(limit=5, delay=3.0)
