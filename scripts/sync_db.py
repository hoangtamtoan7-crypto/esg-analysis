"""同步下载日志到数据库 — 将 download_log.csv 中的成功记录插入 companies 和 reports 表"""

import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "esg_data.db"
DOWNLOAD_LOG_PATH = BASE_DIR / "data" / "download_log.csv"
COMPANY_LIST_PATH = BASE_DIR / "data" / "company_list.csv"


def main():
    # 加载公司列表，建立 code -> (name, exchange, market) 映射
    company_map = {}
    with open(COMPANY_LIST_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["code"].strip()
            company_map[code] = (
                row["name"].strip(),
                row.get("exchange", "").strip(),
                row.get("market", "").strip(),
            )

    # 加载成功下载记录
    success_records = []
    with open(DOWNLOAD_LOG_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("status", "").strip() == "success":
                success_records.append(row)

    print(f"下载日志成功记录: {len(success_records)}")

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    companies_inserted = 0
    companies_skipped = 0
    reports_inserted = 0
    reports_skipped = 0
    errors = []

    for rec in success_records:
        code = rec["code"].strip()
        name = rec.get("name", "").strip()
        year_str = rec.get("year", "").strip()
        filepath = rec.get("filepath", "").strip()
        title = rec.get("title", "").strip()

        if not code or not name:
            continue

        # 从 company_list.csv 获取更完整的公司信息
        exchange = ""
        market = ""
        if code in company_map:
            name_csv, exchange, market = company_map[code]
            if name_csv:
                name = name_csv  # 使用 company_list 中的标准名称

        year = int(year_str) if year_str.isdigit() else 0
        if year == 0:
            errors.append(f"无法解析年份: {code} {name} year={year_str}")
            continue

        # 清理文件路径为相对路径
        if "data\\pdfs\\" in filepath:
            filepath = "data/pdfs/" + filepath.split("data\\pdfs\\")[-1].replace("\\", "/")
        elif "data/pdfs/" not in filepath:
            filepath = f"data/pdfs/{code}_{name}_{year}.pdf"

        # 检查公司是否已存在
        cursor.execute("SELECT id FROM companies WHERE stock_code = ?", (code,))
        row = cursor.fetchone()
        if row:
            company_id = row[0]
            companies_skipped += 1
        else:
            cursor.execute(
                "INSERT INTO companies (stock_code, name, exchange, market) VALUES (?, ?, ?, ?)",
                (code, name, exchange, market),
            )
            company_id = cursor.lastrowid
            companies_inserted += 1

        # 检查报告是否已存在（同公司同年份）
        cursor.execute(
            "SELECT id FROM reports WHERE company_id = ? AND year = ?",
            (company_id, year),
        )
        row = cursor.fetchone()
        if row:
            reports_skipped += 1
            # 更新 pdf_path 如果之前为空
            cursor.execute(
                "UPDATE reports SET pdf_path = ? WHERE id = ? AND (pdf_path IS NULL OR pdf_path = '')",
                (filepath, row[0]),
            )
        else:
            cursor.execute(
                "INSERT INTO reports (company_id, year, title, pdf_path, extraction_status) VALUES (?, ?, ?, ?, ?)",
                (company_id, year, title[:300] if title else "", filepath, "pending"),
            )
            reports_inserted += 1

    conn.commit()

    # 验证结果
    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM reports")
    total_reports = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT company_id) FROM reports")
    companies_with_reports = cursor.fetchone()[0]

    conn.close()

    print(f"\n同步完成:")
    print(f"  新增公司: {companies_inserted}")
    print(f"  已存在公司: {companies_skipped}")
    print(f"  新增报告: {reports_inserted}")
    print(f"  已存在报告: {reports_skipped}")
    print(f"  数据库公司总数: {total_companies}")
    print(f"  数据库报告总数: {total_reports}")
    print(f"  有报告的公司数: {companies_with_reports}")

    if errors:
        print(f"\n警告 ({len(errors)}):")
        for e in errors[:10]:
            print(f"  - {e}")
        if len(errors) > 10:
            print(f"  ... 还有 {len(errors) - 10} 条")


if __name__ == "__main__":
    main()
