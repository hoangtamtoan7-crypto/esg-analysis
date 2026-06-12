"""分析 data/output/ 下所有 JSON 提取结果的数据覆盖率与完整度"""
import json
import os
import sys
import io
from collections import defaultdict
from pathlib import Path

# Fix Windows GBK encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUTPUT_DIR = Path(r"C:\Users\13765\OneDrive\Desktop\研究生\数据要素\data\output")

# ---- 加载所有 JSON 文件 ----
records = []
missing_files = []
for fpath in sorted(OUTPUT_DIR.glob("*_result.json")):
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            data["_file"] = fpath.name
            records.append(data)
    except Exception as e:
        missing_files.append((fpath.name, str(e)))

print(f"成功加载: {len(records)} 条记录")
if missing_files:
    print(f"加载失败: {len(missing_files)} 个文件")

# ---- 1. 公司统计 ----
companies = defaultdict(list)
for r in records:
    companies[r["company_name"]].append(r["report_year"])

print(f"\n{'='*60}")
print(f"一、公司概览")
print(f"{'='*60}")
print(f"公司总数: {len(companies)}")

# 每个公司的年份数
company_year_counts = {name: len(years) for name, years in companies.items()}
# 按年份数分组
year_dist = defaultdict(list)
for name, cnt in company_year_counts.items():
    year_dist[cnt].append(name)

print(f"\n年份覆盖分布:")
for cnt in sorted(year_dist.keys(), reverse=True):
    names = year_dist[cnt]
    print(f"  {cnt}年: {len(names)}家公司")

# 只有1-2年的公司
few_year = sum(len(v) for k, v in year_dist.items() if k <= 2)
print(f"\n只有1-2年数据的公司: {few_year}家/{len(companies)}家 ({few_year*100/len(companies):.1f}%)")

# ---- 2. 年份统计 ----
year_counts = defaultdict(int)
for r in records:
    year_counts[r["report_year"]] += 1

print(f"\n{'='*60}")
print(f"二、年份分布")
print(f"{'='*60}")
for yr in sorted(year_counts.keys()):
    bar = "█" * max(1, year_counts[yr] // 5)
    print(f"  {yr}: {year_counts[yr]:>4} 家公司 {bar}")
total_records = sum(year_counts.values())
print(f"  总计: {total_records} 条记录 (公司×年份)")

# ---- 3. 指标统计 ----
# 定量指标
all_quant_ids = set()
for r in records:
    for ind in r.get("quantitative_indicators", []):
        all_quant_ids.add(ind["id"])

quant_coverage = defaultdict(lambda: {"filled": 0, "total": 0})
for r in records:
    for ind in r.get("quantitative_indicators", []):
        iid = ind["id"]
        quant_coverage[iid]["total"] += 1
        if ind.get("value") is not None:
            quant_coverage[iid]["filled"] += 1

# 定性指标
all_qual_ids = set()
qual_coverage = defaultdict(lambda: {"found": 0, "not_found": 0})
for r in records:
    for ind in r.get("qualitative_indicators", []):
        iid = ind["id"]
        all_qual_ids.add(iid)
        # Qualitative uses "status" field: "yes", "partial", "no"
        status = ind.get("status", ind.get("found", False))
        if status and status != "no":
            qual_coverage[iid]["found"] += 1
        else:
            qual_coverage[iid]["not_found"] += 1

# ---- 4. 定量指标覆盖率 ----
print(f"\n{'='*60}")
print(f"三、定量指标覆盖率 (按指标)")
print(f"{'='*60}")
print(f"定量指标总数: {len(all_quant_ids)} (定义31个)")

# 映射 id -> name
quant_id_to_name = {}
for r in records:
    for ind in r.get("quantitative_indicators", []):
        quant_id_to_name[ind["id"]] = ind["name"]
    if len(quant_id_to_name) == len(all_quant_ids):
        break

dim_map = {"E": "环境", "S": "社会", "G": "治理"}
# 按维度排序
def sort_key(iid):
    dim = iid.split("_")[0]
    return dim + iid

quant_rows = []
for iid in sorted(all_quant_ids, key=sort_key):
    stats = quant_coverage[iid]
    pct = stats["filled"] * 100 / stats["total"] if stats["total"] > 0 else 0
    name = quant_id_to_name.get(iid, iid)
    dim = iid.split("_")[0]
    quant_rows.append((iid, name, dim, stats["filled"], stats["total"], pct))

for row in quant_rows:
    iid, name, dim, filled, total, pct = row
    bar = "#" * int(pct/5) + "." * (20 - int(pct/5))
    print(f"  [{dim}] {iid} {name}: {filled}/{total} ({pct:.1f}%) {bar}")

# ---- 5. 定性指标覆盖率 ----
print(f"\n{'='*60}")
print(f"四、定性指标覆盖率 (按指标)")
print(f"{'='*60}")
print(f"定性指标总数: {len(all_qual_ids)} (定义18个)")

qual_id_to_name = {}
for r in records:
    for ind in r.get("qualitative_indicators", []):
        qual_id_to_name[ind["id"]] = ind["name"]
    if len(qual_id_to_name) == len(all_qual_ids):
        break

qual_rows = []
for iid in sorted(all_qual_ids, key=sort_key):
    stats = qual_coverage[iid]
    total = stats["found"] + stats["not_found"]
    pct = stats["found"] * 100 / total if total > 0 else 0
    name = qual_id_to_name.get(iid, iid)
    dim = iid.split("_")[0]
    qual_rows.append((iid, name, dim, stats["found"], total, pct))

for row in qual_rows:
    iid, name, dim, found, total, pct = row
    bar = "#" * int(pct/5) + "." * (20 - int(pct/5))
    print(f"  [{dim}] {iid} {name}: {found}/{total} ({pct:.1f}%) {bar}")

# ---- 6. 按维度汇总 ----
print(f"\n{'='*60}")
print(f"五、按维度汇总")
print(f"{'='*60}")

for dim_code, dim_name in [("E", "环境"), ("S", "社会"), ("G", "治理")]:
    # 定量
    q_filled = sum(stats["filled"] for iid, stats in quant_coverage.items() if iid.startswith(dim_code))
    q_total = sum(stats["total"] for iid, stats in quant_coverage.items() if iid.startswith(dim_code))
    q_pct = q_filled * 100 / q_total if q_total > 0 else 0
    # 定性
    l_found = sum(stats["found"] for iid, stats in qual_coverage.items() if iid.startswith(dim_code))
    l_total = sum(stats["found"] + stats["not_found"] for iid, stats in qual_coverage.items() if iid.startswith(dim_code))
    l_pct = l_found * 100 / l_total if l_total > 0 else 0
    # 总体
    all_filled = q_filled + l_found
    all_total = q_total + l_total
    all_pct = all_filled * 100 / all_total if all_total > 0 else 0

    print(f"\n  {dim_name}({dim_code}):")
    print(f"    定量: {q_filled}/{q_total} ({q_pct:.1f}%)")
    print(f"    定性: {l_found}/{l_total} ({l_pct:.1f}%)")
    print(f"    综合: {all_filled}/{all_total} ({all_pct:.1f}%)")

# ---- 7. 每家公司每年的数据完整度 ----
print(f"\n{'='*60}")
print(f"七、公司数据完整度 Top 10 & Bottom 10")
print(f"{'='*60}")

company_completeness = []  # (company, year, quant_pct, qual_pct, overall_pct)
for r in records:
    cn = r["company_name"]
    yr = r["report_year"]
    # 定量
    q_filled = sum(1 for ind in r.get("quantitative_indicators", []) if ind.get("value") is not None)
    q_total = len(r.get("quantitative_indicators", []))
    # 定性
    l_found = sum(1 for ind in r.get("qualitative_indicators", []) if (ind.get("status") or ind.get("found")) and ind.get("status") != "no")
    l_total = len(r.get("qualitative_indicators", []))
    overall_pct = (q_filled + l_found) * 100 / (q_total + l_total) if (q_total + l_total) > 0 else 0
    company_completeness.append((cn, yr, q_filled, q_total, l_found, l_total, overall_pct))

company_completeness.sort(key=lambda x: x[6], reverse=True)

print("\n完整度最高的 15 条记录:")
for i, (cn, yr, qf, qt, lf, lt, pct) in enumerate(company_completeness[:15], 1):
    print(f"  {i:>2}. {cn} ({yr}): {pct:.1f}% (定量{qf}/{qt}, 定性{lf}/{lt})")

print("\n完整度最低的 15 条记录:")
for i, (cn, yr, qf, qt, lf, lt, pct) in enumerate(company_completeness[-15:], 1):
    print(f"  {i:>2}. {cn} ({yr}): {pct:.1f}% (定量{qf}/{qt}, 定性{lf}/{lt})")

# ---- 8. 平均完整度 ----
avg_q = sum(c[2] for c in company_completeness) / sum(c[3] for c in company_completeness) * 100
avg_l = sum(c[4] for c in company_completeness) / sum(c[5] for c in company_completeness) * 100
avg_all = sum(c[6] for c in company_completeness) / len(company_completeness)

print(f"\n{'='*60}")
print(f"八、总体统计")
print(f"{'='*60}")
print(f"  公司总数: {len(companies)}")
print(f"  提取记录总数: {len(records)}")
print(f"  年份跨度: {min(year_counts.keys())} - {max(year_counts.keys())}")
print(f"  定量指标定义数: {len(all_quant_ids)}")
print(f"  定性指标定义数: {len(all_qual_ids)}")
print(f"  指标定义总数: {len(all_quant_ids) + len(all_qual_ids)}")
print(f"  定量指标平均填充率: {avg_q:.1f}%")
print(f"  定性指标平均发现率: {avg_l:.1f}%")
print(f"  整体平均完整度: {avg_all:.1f}%")

# 年份覆盖率(有多少公司有该年数据)
print(f"\n  各年份公司数量:")
for yr in sorted(year_counts.keys()):
    pct = year_counts[yr] * 100 / len(companies)
    print(f"    {yr}: {year_counts[yr]}家/{len(companies)}家 ({pct:.1f}%)")

# 哪些公司各年份覆盖最好的
print(f"\n  年份覆盖最全的公司 (Top 20):")
company_fullness = sorted(company_year_counts.items(), key=lambda x: x[1], reverse=True)
for i, (name, cnt) in enumerate(company_fullness[:20], 1):
    yrs = sorted(companies[name])
    print(f"    {i:>2}. {name}: {cnt}年 ({yrs[0]}-{yrs[-1]})")
