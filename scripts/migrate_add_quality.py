"""数据库迁移：为reports表添加quality_score和completeness列，并从JSON回填"""
import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "esg_data.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. 添加列（如果不存在）
cols = [row[1] for row in cursor.execute("PRAGMA table_info(reports)").fetchall()]
for col in ["quality_score", "completeness"]:
    if col not in cols:
        cursor.execute(f"ALTER TABLE reports ADD COLUMN {col} FLOAT DEFAULT 0.0")
        print(f"Added column: {col}")
    else:
        print(f"Column already exists: {col}")

# 2. 建立JSON索引：按stock_code -> JSON path
json_index = {}
for f in os.listdir(OUTPUT_DIR):
    if f.endswith("_result.json"):
        stock_code = f.split("_")[0]
        json_index[stock_code] = os.path.join(OUTPUT_DIR, f)

# 也建立精确文件名索引
json_by_name = {f: os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith("_result.json")}

print(f"JSON files indexed: {len(json_index)} by stock_code")

# 3. 回填：用 stock_code + year 匹配
cursor.execute("""
    SELECT r.id, r.md_path, c.stock_code, r.year
    FROM reports r
    JOIN companies c ON r.company_id = c.id
    WHERE r.extraction_status = 'done'
""")

updated = 0
missed = 0
for row in cursor.fetchall():
    report_id, md_path, stock_code, year = row
    json_path = None

    # Strategy 1: stock_code match (most reliable)
    json_path = json_index.get(stock_code)

    # Strategy 2: if md_path is a known result JSON name
    if not json_path and md_path:
        md_basename = os.path.basename(md_path)
        # md_path might be "000001_平安银行_2026.md" or "000001_平安银行_2026_result.json"
        result_name = md_basename.replace(".md", "_result.json").replace("_result_result.json", "_result.json")
        json_path = json_by_name.get(result_name)

    # Strategy 3: fuzzy match by md_path stem
    if not json_path and md_path:
        md_stem = os.path.splitext(os.path.basename(md_path))[0]
        md_stem = md_stem.replace("_result", "")
        for k, v in json_by_name.items():
            if md_stem in k or k.startswith(stock_code):
                json_path = v
                break

    if not json_path:
        missed += 1
        continue

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        missed += 1
        continue

    validation = data.get("validation", {})
    completeness_data = data.get("completeness", {})
    quality = validation.get("overall_quality_score", 0)
    complete = completeness_data.get("completeness", 0)

    cursor.execute(
        "UPDATE reports SET quality_score = ?, completeness = ? WHERE id = ?",
        (quality, complete, report_id),
    )
    updated += 1

conn.commit()

# 4. 验证
cursor.execute("SELECT COUNT(*) FROM reports WHERE quality_score > 0")
has_quality = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM reports WHERE extraction_status = 'done'")
done = cursor.fetchone()[0]
print(f"\nUpdated: {updated}")
print(f"Missed: {missed}")
print(f"Reports with quality data: {has_quality}/{done}")
cursor.execute("SELECT AVG(quality_score), AVG(completeness) FROM reports WHERE quality_score > 0")
avg_q, avg_c = cursor.fetchone()
print(f"Avg quality_score: {avg_q:.4f}")
print(f"Avg completeness: {avg_c:.1f}%")

# 5. 质量分分布
cursor.execute("""
    SELECT
        CASE WHEN quality_score >= 0.8 THEN '0.8-1.0 优秀'
             WHEN quality_score >= 0.6 THEN '0.6-0.8 良好'
             WHEN quality_score >= 0.4 THEN '0.4-0.6 一般'
             WHEN quality_score > 0 THEN '>0-0.4 较差'
             ELSE '无数据'
        END as band,
        COUNT(*) as cnt
    FROM reports
    WHERE extraction_status = 'done'
    GROUP BY band
    ORDER BY band
""")
print("\n质量分分布:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print("\nMigration complete!")
