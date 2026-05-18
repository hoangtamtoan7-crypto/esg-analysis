"""补充遗漏的PDF到数据库"""
import sqlite3
import os
import re
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "esg_data.db")
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")
COMPANY_LIST_PATH = os.path.join(BASE_DIR, "data", "company_list.csv")

# 加载公司列表
company_map = {}
with open(COMPANY_LIST_PATH, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        code = row["code"].strip()
        company_map[code] = (
            row["name"].strip(),
            row.get("exchange", "").strip(),
            row.get("market", "").strip(),
        )

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# 检查磁盘PDF和DB报告的差异
cursor.execute("SELECT pdf_path FROM reports WHERE pdf_path IS NOT NULL AND pdf_path != ''")
db_pdf_filenames = set()
for row in cursor:
    fn = row[0].replace("data/pdfs/", "").replace("\\", "/")
    db_pdf_filenames.add(fn)

disk_pdfs = set(os.listdir(PDF_DIR))
missing_in_db = disk_pdfs - db_pdf_filenames

# 提取缺失PDF的股票代码
to_add = []
for pdf_name in sorted(missing_in_db):
    code = pdf_name.split("_")[0]
    # 从文件名提取年份
    year_match = re.search(r"_(\d{4})\.pdf$", pdf_name)
    year = int(year_match.group(1)) if year_match else 0
    to_add.append((code, pdf_name, year))
    print(f"需补充: {code} -> {pdf_name} (年份: {year})")

companies_added = 0
reports_added = 0

for code, pdf_name, year in to_add:
    # 检查公司是否存在
    cursor.execute("SELECT id FROM companies WHERE stock_code = ?", (code,))
    company_row = cursor.fetchone()

    if not company_row:
        # 从company_list获取公司名
        name, exchange, market = "Unknown", "", ""
        if code in company_map:
            name, exchange, market = company_map[code]
        else:
            # 从PDF文件名提取
            name = pdf_name.split("_", 1)[1].rsplit("_", 1)[0] if "_" in pdf_name else code

        cursor.execute(
            "INSERT INTO companies (stock_code, name, exchange, market) VALUES (?, ?, ?, ?)",
            (code, name, exchange, market),
        )
        company_id = cursor.lastrowid
        companies_added += 1
        print(f"  新增公司: {code} {name}")
    else:
        company_id = company_row[0]

    # 检查报告是否已存在
    pdf_path = f"data/pdfs/{pdf_name}"
    cursor.execute(
        "SELECT id FROM reports WHERE company_id = ? AND year = ?",
        (company_id, year),
    )
    report_row = cursor.fetchone()

    if not report_row:
        cursor.execute(
            "INSERT INTO reports (company_id, year, title, pdf_path, extraction_status) VALUES (?, ?, ?, ?, ?)",
            (company_id, year, "", pdf_path, "pending"),
        )
        reports_added += 1
        print(f"  新增报告: {pdf_path}")

db.commit()

# 最终统计
cursor.execute("SELECT COUNT(*) FROM companies")
print(f"\n最终: 公司 {cursor.fetchone()[0]}, ", end="")
cursor.execute("SELECT COUNT(*) FROM reports")
print(f"报告 {cursor.fetchone()[0]}, ", end="")
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'done'")
print(f"已提取 {cursor.fetchone()[0]}, ", end="")
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'pending'")
print(f"待提取 {cursor.fetchone()[0]}")

# 再次检查差异
cursor.execute("SELECT pdf_path FROM reports WHERE pdf_path IS NOT NULL AND pdf_path != ''")
db_pdf_filenames2 = set()
for row in cursor:
    fn = row[0].replace("data/pdfs/", "").replace("\\", "/")
    db_pdf_filenames2.add(fn)

still_missing = disk_pdfs - db_pdf_filenames2
if still_missing:
    print(f"\n仍有 {len(still_missing)} 个PDF未关联:")
    for f in sorted(still_missing):
        print(f"  {f}")
else:
    print("\n所有PDF均已关联到数据库")

db.close()
