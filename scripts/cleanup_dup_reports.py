"""删除重复报告，迁移提取数据到正确记录"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "esg_data.db"
PDF_DIR = BASE_DIR / "data" / "pdfs"

disk_pdfs = set(os.listdir(str(PDF_DIR)))
conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

# 找出所有bad path的报告
cursor.execute("SELECT id, pdf_path, company_id, year FROM reports WHERE pdf_path IS NOT NULL AND pdf_path != ''")
bad_ids = []
for row in cursor:
    rid, pdf_path, company_id, year = row
    fn = pdf_path.replace("data/pdfs/", "").replace("\\", "/")
    if fn not in disk_pdfs:
        bad_ids.append((rid, fn, company_id, year))

print(f"Bad reports: {len(bad_ids)}")

migrated_values = 0
migrated_texts = 0
deleted = 0

for bad_id, bad_fn, company_id, year in bad_ids:
    # Find good duplicate
    cursor.execute(
        "SELECT id FROM reports WHERE company_id = ? AND year = ? AND id != ?",
        (company_id, year, bad_id)
    )
    good = cursor.fetchone()
    if not good:
        print(f"  No good duplicate for id={bad_id} ({bad_fn}), keeping")
        continue

    good_id = good[0]

    # Migrate extracted_values
    cursor.execute(
        "UPDATE extracted_values SET report_id = ? WHERE report_id = ?",
        (good_id, bad_id)
    )
    migrated_values += cursor.rowcount

    # Migrate extracted_texts
    cursor.execute(
        "UPDATE extracted_texts SET report_id = ? WHERE report_id = ?",
        (good_id, bad_id)
    )
    migrated_texts += cursor.rowcount

    # Delete bad report
    cursor.execute("DELETE FROM reports WHERE id = ?", (bad_id,))
    deleted += 1

conn.commit()

print(f"Migrated: {migrated_values} values, {migrated_texts} texts")
print(f"Deleted: {deleted} duplicate reports")

# Verify
cursor.execute("SELECT COUNT(*) FROM reports")
total = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'done'")
done = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'pending' OR extraction_status IS NULL")
pending = cursor.fetchone()[0]
print(f"Final: {total} reports ({done} done, {pending} pending)")

# Check disk vs db again
cursor.execute("SELECT pdf_path FROM reports WHERE pdf_path IS NOT NULL AND pdf_path != ''")
db_pdfs = set()
for row in cursor:
    fn = row[0].replace("data/pdfs/", "").replace("\\", "/")
    db_pdfs.add(fn)

missing = disk_pdfs - db_pdfs
extra = db_pdfs - disk_pdfs
print(f"Missing from DB: {len(missing)}")
print(f"Missing from disk: {len(extra)}")
if extra:
    print("Extra in DB (not on disk):")
    for f in sorted(extra)[:10]:
        print(f"  {f}")

conn.close()
