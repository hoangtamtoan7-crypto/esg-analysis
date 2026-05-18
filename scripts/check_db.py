"""检查数据库与PDF目录的一致性"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "esg_data.db")
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

cursor.execute("SELECT pdf_path FROM reports WHERE pdf_path IS NOT NULL AND pdf_path != ''")
db_pdfs = set()
for row in cursor:
    filename = row[0].replace("data/pdfs/", "").replace("\\", "/")
    db_pdfs.add(filename)

disk_pdfs = set(os.listdir(PDF_DIR))

missing_in_db = disk_pdfs - db_pdfs
missing_on_disk = db_pdfs - disk_pdfs

print(f"PDFs on disk: {len(disk_pdfs)}")
print(f"PDFs in DB reports: {len(db_pdfs)}")
print(f"Missing from DB: {len(missing_in_db)}")
print(f"Missing from disk: {len(missing_on_disk)}")

if missing_in_db:
    print("\nPDFs on disk but NOT in DB (first 20):")
    for f in sorted(missing_in_db)[:20]:
        print(f"  {f}")

if missing_on_disk:
    print("\nPDFs in DB but NOT on disk (first 20):")
    for f in sorted(missing_on_disk)[:20]:
        print(f"  {f}")

# Check companies/reports stats
cursor.execute("SELECT COUNT(*) FROM companies")
print(f"\nCompanies: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM reports")
print(f"Reports: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'done'")
print(f"Extracted (done): {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'pending'")
print(f"Pending extraction: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM extracted_values")
print(f"Extracted values: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM extracted_texts")
print(f"Extracted texts: {cursor.fetchone()[0]}")

db.close()
