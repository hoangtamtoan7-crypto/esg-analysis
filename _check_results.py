"""检查提取结果的质量和统计信息"""
import json
from pathlib import Path

result_dir = Path("data/output")
results = sorted(result_dir.glob("*_result.json"))

total_qt = 0
total_ql = 0
qt_with_value = 0
ql_with_status = 0
companies = []

for rp in results:
    with open(rp, "r", encoding="utf-8") as f:
        r = json.load(f)

    qt = r.get("quantitative_indicators", [])
    ql = r.get("qualitative_indicators", [])
    total_qt += len(qt)
    total_ql += len(ql)

    qt_val = sum(1 for item in qt if item.get("value") is not None)
    ql_val = sum(1 for item in ql if item.get("status") in ("yes", "partial"))
    qt_with_value += qt_val
    ql_with_status += ql_val

    companies.append({
        "name": r.get("company_name", ""),
        "year": r.get("report_year", ""),
        "qt_total": len(qt),
        "qt_found": qt_val,
        "ql_total": len(ql),
        "ql_found": ql_val,
    })

print(f"Total reports: {len(results)}")
print(f"Quantitative indicators found: {qt_with_value}/{total_qt}")
print(f"Qualitative indicators found (yes/partial): {ql_with_status}/{total_ql}")
print(f"Quantitative extraction rate: {qt_with_value/max(total_qt,1)*100:.1f}%")
print(f"Qualitative extraction rate: {ql_with_status/max(total_ql,1)*100:.1f}%")

# Top companies with most data found
companies.sort(key=lambda c: c["qt_found"] + c["ql_found"], reverse=True)
print("\nTop 10 companies by indicator coverage:")
for c in companies[:10]:
    total = c["qt_total"] + c["ql_total"]
    found = c["qt_found"] + c["ql_found"]
    print(f"  {c['name']} ({c['year']}): {found}/{total} found")

print("\nBottom 5 companies (likely scanned PDFs or poor extraction):")
for c in companies[-5:]:
    total = c["qt_total"] + c["ql_total"]
    found = c["qt_found"] + c["ql_found"]
    print(f"  {c['name']} ({c['year']}): {found}/{total} found")

# Show one good result in detail
print("\n=== Sample: 贵州茅台 Quantitative ===")
maotai = None
for rp in results:
    if "茅台" in rp.stem:
        with open(rp, "r", encoding="utf-8") as f:
            maotai = json.load(f)
        break

if maotai:
    for item in maotai.get("quantitative_indicators", [])[:15]:
        val = item.get("value")
        if val is not None:
            print(f"  [{item['id']}] {item['name']}: {val} {item.get('unit','')} | conf={item.get('confidence','')}")
    print("\n=== Sample: 贵州茅台 Qualitative ===")
    for item in maotai.get("qualitative_indicators", []):
        print(f"  [{item['id']}] {item['name']}: {item.get('status','')} | {item.get('summary','')[:80]}")
