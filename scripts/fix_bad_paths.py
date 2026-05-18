"""清理数据库中错误的PDF路径"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "esg_data.db"
PDF_DIR = BASE_DIR / "data" / "pdfs"

disk_pdfs = set(os.listdir(str(PDF_DIR)))
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

cursor.execute("SELECT id, pdf_path, extraction_status FROM reports WHERE pdf_path IS NOT NULL AND pdf_path != ''")
bad_reports = []
for row in cursor:
    fn = row[1].replace("data/pdfs/", "").replace("\\", "/")
    if fn not in disk_pdfs:
        bad_reports.append((row[0], fn, row[2]))

print(f"Reports with bad PDF paths: {len(bad_reports)}")

# Check which have extracted data
has_data = 0
no_data = 0
for rid, fn, status in bad_reports:
    cursor.execute("SELECT COUNT(*) FROM extracted_values WHERE report_id = ?", (rid,))
    vals = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM extracted_texts WHERE report_id = ?", (rid,))
    texts = cursor.fetchone()[0]
    if vals > 0 or texts > 0:
        has_data += 1
    else:
        no_data += 1

print(f"  Has extracted data: {has_data}")
print(f"  No extracted data: {no_data}")

# Show first few
for rid, fn, status in bad_reports[:5]:
    print(f"  id={rid}  path={fn[:60]}  status={status}")

# If there are dups (same company+year with good path too), delete bad ones
print("\n--- Looking for duplicates ---")
for rid, fn, status in bad_reports:
    cursor.execute("SELECT company_id, year FROM reports WHERE id = ?", (rid,))
    row = cursor.fetchone()
    if not row:
        continue
    company_id, year = row
    cursor.execute(
        "SELECT id, pdf_path FROM reports WHERE company_id = ? AND year = ? AND id != ?",
        (company_id, year, rid)
    )
    dup = cursor.fetchone()
    if dup:
        print(f"  Dup: bad={rid}({fn[:40]}) good={dup[0]}({dup[1][:40] if dup[1] else 'N/A'})")

conn.close()
