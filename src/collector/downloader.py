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
DEFAULT_YEAR_RANGE = range(2019, 2027)  # 2019-2026


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
        """加载已有下载日志，实现断点续传（按 股票代码+年份 跳过已成功的）"""
        if not DOWNLOAD_LOG_PATH.exists():
            return
        try:
            with open(DOWNLOAD_LOG_PATH, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    code = row.get("code", "")
                    status = row.get("status", "")
                    year = row.get("year", "")
                    if code:
                        self.download_log.append(row)
                        key = f"{code}_{year}"
                        if status == "success" and year:
                            self.processed_codes.add(key)
            logger.info(f"断点续传: 已加载 {len(self.download_log)} 条记录，跳过 {len(self.processed_codes)} 个已成功(按代码+年份)")
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
        """下载PDF并验证。如果目标文件已存在则跳过"""
        if filepath.exists() and filepath.stat().st_size > 10_000:
            logger.info(f"已存在，跳过: {filepath.name}")
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

    def _extract_year(self, ann: dict) -> str:
        """从公告时间戳提取年份"""
        from datetime import datetime
        ts = ann.get("announcementTime", 0)
        if ts:
            return datetime.fromtimestamp(ts / 1000).strftime("%Y")
        return ""

    def _collect_announcements(self, stock_code: str) -> list:
        """收集一家公司的所有ESG相关公告"""
        all_announcements = []
        seen_ids = set()

        for keyword in ESG_KEYWORDS_FAST:
            announcements = self.search(stock_code, keyword)
            for ann in announcements:
                aid = ann.get("announcementId", "")
                if aid and aid not in seen_ids:
                    seen_ids.add(aid)
                    all_announcements.append(ann)
            time.sleep(0.3)

        if not all_announcements:
            for keyword in ESG_KEYWORDS_REST:
                announcements = self.search(stock_code, keyword)
                for ann in announcements:
                    aid = ann.get("announcementId", "")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        all_announcements.append(ann)
                time.sleep(0.3)

        return all_announcements

    def find_and_download_multi_year(
        self, stock_code: str, company_name: str,
        year_range: range = DEFAULT_YEAR_RANGE,
    ) -> list:
        """为一家公司搜索并下载多个年度的ESG报告

        Returns:
            成功下载的文件路径列表
        """
        safe_name = _sanitize_filename(company_name)
        all_announcements = self._collect_announcements(stock_code)

        if not all_announcements:
            self.download_log.append({
                "code": stock_code, "name": company_name,
                "title": "", "year": "all", "status": "no_esg_report",
            })
            return []

        # 过滤有效公告
        valid = [ann for ann in all_announcements if self._is_valid_announcement(ann)]

        # 按年份分组，每年取最佳匹配（非英文、最新）
        from collections import defaultdict
        by_year = defaultdict(list)
        for ann in valid:
            yr = self._extract_year(ann)
            if yr:
                by_year[yr].append(ann)

        downloaded = []
        # 按目标年份范围逐一处理
        for target_year in sorted(year_range, reverse=True):
            target_str = str(target_year)
            log_key = f"{stock_code}_{target_str}"
            if log_key in self.processed_codes:
                continue

            candidates = by_year.get(target_str, [])
            if not candidates:
                # 尝试从标题匹配年份
                candidates = [
                    ann for ann in valid
                    if target_str in _clean_title(ann.get("announcementTitle", ""))
                ]

            if not candidates:
                self.download_log.append({
                    "code": stock_code, "name": company_name,
                    "title": f"无{target_year}年度报告", "year": target_str,
                    "status": "no_report_for_year",
                })
                continue

            # 选最佳：非英文版本优先，时间最近的优先
            candidates.sort(
                key=lambda a: (
                    "英文" in _clean_title(a.get("announcementTitle", "")),
                    -(a.get("announcementTime", 0) or 0),
                )
            )

            best = candidates[0]
            title = _clean_title(best.get("announcementTitle", ""))
            adjunct_url = best.get("adjunctUrl", "")
            pdf_url = self._build_pdf_url(adjunct_url)

            filename = f"{stock_code}_{safe_name}_{target_str}.pdf"
            filepath = PDF_DIR / filename

            logger.info(f"下载 [{target_str}]: {company_name} — {title[:50]}")
            if self.download_pdf(pdf_url, filepath, stock_code):
                self.download_log.append({
                    "code": stock_code, "name": company_name,
                    "title": title, "year": target_str,
                    "filepath": str(filepath), "status": "success",
                })
                downloaded.append(filepath)
            else:
                self.download_log.append({
                    "code": stock_code, "name": company_name,
                    "title": title, "year": target_str, "status": "download_failed",
                })

        if not downloaded and not any(
            e["code"] == stock_code and e["year"] != "all"
            for e in self.download_log[-20:]
        ):
            self.download_log.append({
                "code": stock_code, "name": company_name,
                "title": "", "year": "all", "status": "no_valid_pdf",
            })

        return downloaded

    def find_and_download(
        self, stock_code: str, company_name: str, year: str = "2025"
    ) -> Optional[Path]:
        """为一家公司搜索并下载最新的ESG报告（单年份模式，向后兼容）"""
        paths = self.find_and_download_multi_year(
            stock_code, company_name,
            year_range=range(int(year), int(year) + 1),
        )
        return paths[0] if paths else None

    def run(self, limit: Optional[int] = None, delay: float = 1.0,
            year_range: range = DEFAULT_YEAR_RANGE):
        """批量下载ESG报告（多年度模式，支持断点续传）

        Args:
            limit: 限制处理的股票数量（用于测试）
            delay: 搜索间隔时间
            year_range: 目标年份范围，默认 2019-2026
        """
        companies = self._load_company_list()
        years_list = list(year_range)
        logger.info(f"目标年份范围: {years_list[0]}-{years_list[-1]} ({len(years_list)}个年份)")

        # 过滤已处理的公司（所有年份都成功才跳过整家公司）
        new_companies = [
            c for c in companies
            if not all(f"{c['code']}_{yr}" in self.processed_codes for yr in years_list)
        ]
        skipped = len(companies) - len(new_companies)
        if skipped:
            logger.info(f"断点续传: 跳过 {skipped} 家已完成所有年份的公司，剩余 {len(new_companies)} 家")

        if limit:
            new_companies = new_companies[:limit]

        logger.info(f"开始下载 {len(new_companies)} 家公司的ESG报告（{len(years_list)}个年份）...")
        total_downloaded = 0
        total_no_report = 0
        total_failed = 0

        for i, row in enumerate(tqdm(new_companies, desc="下载ESG报告")):
            code = row["code"]
            name = row["name"]
            downloaded = self.find_and_download_multi_year(code, name, year_range)
            total_downloaded += len(downloaded)

            # 统计该公司的结果
            for entry in self.download_log[-len(years_list):]:
                st = entry.get("status", "")
                if st == "no_report_for_year":
                    total_no_report += 1
                elif st in ("download_failed", "no_valid_pdf"):
                    total_failed += 1

            time.sleep(delay)

            if (i + 1) % SAVE_INTERVAL == 0:
                self._save_log()
                logger.info(
                    f"进度: {i+1}/{len(new_companies)} "
                    f"已下载:{total_downloaded} 无报告:{total_no_report} 失败:{total_failed}"
                )

        self._save_log()
        logger.info(
            f"下载完成！已下载PDF: {total_downloaded}, 无对应年份报告: {total_no_report}, 失败: {total_failed}"
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
