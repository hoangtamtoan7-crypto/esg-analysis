"""生成自包含静态HTML ESG分析报告 — 无需服务器，浏览器直接打开"""
import json
from pathlib import Path
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
REPORT_PATH = BASE_DIR / "ESG分析报告.html"

INDUSTRY_MAP = [
    ("银行", "金融"), ("保险", "金融"), ("证券", "金融"), ("太保", "金融"),
    ("财富", "金融"), ("华泰", "金融"), ("同花顺", "金融"),
    ("茅台", "食品饮料"), ("五粮液", "食品饮料"), ("老窖", "食品饮料"),
    ("汾酒", "食品饮料"), ("洋河", "食品饮料"), ("古井", "食品饮料"),
    ("伊利", "食品饮料"), ("海天", "食品饮料"), ("双汇", "食品饮料"), ("啤酒", "食品饮料"),
    ("医药", "医药"), ("制药", "医药"), ("医疗", "医药"), ("药明", "医药"),
    ("爱尔", "医药"), ("白药", "医药"), ("片仔", "医药"),
    ("泰格", "医药"), ("康龙", "医药"), ("智飞", "医药"),
    ("石油", "能源"), ("石化", "能源"), ("煤炭", "能源"), ("神华", "能源"),
    ("电力", "能源"), ("核电", "能源"), ("煤业", "能源"), ("兖矿", "能源"), ("华能", "能源"),
    ("科技", "科技"), ("海康", "科技"), ("大华", "科技"), ("讯飞", "科技"),
    ("金山", "科技"), ("京东方", "科技"), ("紫光", "科技"), ("立讯", "科技"),
    ("蓝思", "科技"), ("圣邦", "科技"), ("卓胜", "科技"), ("兆易", "科技"),
    ("中微", "科技"), ("北方华创", "科技"), ("三环", "科技"),
    ("汇川", "科技"), ("国电南瑞", "科技"), ("TCL", "科技"), ("中兴", "科技"),
    ("传音", "科技"), ("中芯", "科技"),
    ("比亚迪", "汽车"), ("上汽", "汽车"), ("长安汽车", "汽车"),
    ("广汽", "汽车"), ("福耀", "汽车"),
    ("美的", "制造业"), ("格力", "制造业"), ("海尔", "制造业"),
    ("重工", "制造业"), ("三一", "制造业"), ("潍柴", "制造业"),
    ("船舶", "制造业"), ("航发", "制造业"),
    ("钢铁", "材料"), ("钢股份", "材料"), ("特钢", "材料"), ("水泥", "材料"),
    ("化学", "材料"), ("万华", "材料"), ("建材", "材料"), ("雨虹", "材料"),
    ("万科", "房地产"), ("招商蛇口", "房地产"), ("保利", "房地产"), ("中国建筑", "建筑"),
    ("航空", "交通运输"), ("国航", "交通运输"), ("东航", "交通运输"),
    ("南航", "交通运输"), ("机场", "交通运输"), ("铁路", "交通运输"),
    ("顺丰", "交通运输"), ("远洋", "交通运输"), ("中远海控", "交通运输"),
    ("隆基", "新能源"), ("阳光电源", "新能源"), ("通威", "新能源"),
    ("中环", "新能源"), ("赣锋", "新能源"), ("宁德时代", "新能源"),
    ("牧原", "农业"), ("温氏", "农业"), ("海大", "农业"),
    ("分众", "传媒"), ("芒果", "传媒"),
    ("电信", "通信"), ("联通", "通信"), ("移动", "通信"),
]

COLORS = {
    "金融": "#1f77b4", "食品饮料": "#ff7f0e", "医药": "#2ca02c",
    "能源": "#d62728", "科技": "#9467bd", "汽车": "#8c564b",
    "制造业": "#e377c2", "材料": "#7f7f7f", "房地产": "#bcbd22",
    "交通运输": "#17becf", "新能源": "#00cc66", "农业": "#cc6600",
    "传媒": "#ff66cc", "通信": "#6699ff", "建筑": "#996633", "其他": "#aaaaaa",
}


def classify(name):
    for kw, ind in INDUSTRY_MAP:
        if kw in name:
            return ind
    return "其他"


def load_data():
    rows = []
    for f in sorted(OUTPUT_DIR.glob("*_result.json")):
        with open(f, "r", encoding="utf-8") as fp:
            r = json.load(fp)
        company = r.get("company_name", "")
        year = r.get("report_year", "")
        validation = r.get("validation", {})
        completeness = r.get("completeness", {})
        industry = classify(company)
        quality = validation.get("overall_quality_score", 0)
        coverage = completeness.get("completeness", 0)
        if coverage == 0:
            continue
        for item in r.get("quantitative_indicators", []):
            val = item.get("value")
            if val is None or not isinstance(val, (int, float)):
                continue
            rows.append({
                "公司": company, "行业": industry, "年份": year,
                "指标ID": item.get("id"), "指标名称": item.get("name"),
                "数值": val, "单位": item.get("unit"),
                "置信度": item.get("confidence", ""),
                "质量分": quality, "覆盖度": coverage,
            })
    return pd.DataFrame(rows)


def compute_scores(df):
    companies = []
    for name, group in df.groupby("公司"):
        # E
        e_items = group[group["指标ID"].str.startswith("E_")]
        e_score, e_count = 0, 0
        for ind_id in ["E_Q01", "E_Q06", "E_Q10"]:
            vals = e_items[e_items["指标ID"] == ind_id]["数值"]
            if len(vals) > 0 and vals.iloc[0] > 0:
                e_score += 1 if ind_id != "E_Q06" else min(vals.iloc[0] / 100, 1)
                e_count += 1
        e_final = round(e_score / max(e_count, 1), 3)
        # S
        s_items = group[group["指标ID"].str.startswith("S_")]
        s_score, s_count = 0, 0
        for ind_id in ["S_Q05", "S_Q08", "S_Q02"]:
            vals = s_items[s_items["指标ID"] == ind_id]["数值"]
            if len(vals) > 0:
                if ind_id == "S_Q05":
                    s_score += min(vals.iloc[0] / 100, 1)
                elif ind_id == "S_Q08":
                    s_score += min(vals.iloc[0] / 20, 1)
                elif ind_id == "S_Q02":
                    s_score += min(vals.iloc[0] / 50, 1)
                s_count += 1
        s_final = round(s_score / max(s_count, 1), 3)
        # G
        g_items = group[group["指标ID"].str.startswith("G_")]
        g_score, g_count = 0, 0
        for ind_id in ["G_Q02", "G_Q04"]:
            vals = g_items[g_items["指标ID"] == ind_id]["数值"]
            if len(vals) > 0:
                g_score += min(vals.iloc[0] / (50 if ind_id == "G_Q02" else 12), 1)
                g_count += 1
        g_final = round(g_score / max(g_count, 1), 3)
        esg = round((e_final + s_final + g_final) / 3, 3)
        companies.append({
            "公司": name, "行业": group["行业"].iloc[0],
            "E": e_final, "S": s_final, "G": g_final, "ESG": esg,
        })
    result = pd.DataFrame(companies).sort_values("ESG", ascending=False).reset_index(drop=True)
    result.index = result.index + 1
    result.index.name = "排名"
    return result


def generate():
    print("Loading data...")
    df = load_data()
    scores = compute_scores(df)
    companies_n = df["公司"].nunique()
    industries_n = df["行业"].nunique()

    # ===== Build charts =====
    charts = []

    # 1) ESG Top 20 bar chart
    top20 = scores.head(20).copy()
    top20["公司"] = pd.Categorical(top20["公司"], categories=top20["公司"][::-1], ordered=True)
    fig1 = px.bar(top20, x="ESG", y="公司", orientation="h", color="行业",
                  color_discrete_map=COLORS, title="ESG综合得分 TOP20",
                  text=top20["ESG"].apply(lambda x: f"{x:.3f}"))
    fig1.update_traces(textposition="outside")
    fig1.update_layout(height=550, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(fig1.to_html(full_html=False, include_plotlyjs=False))

    # 2) Industry average ESG
    ind_avg = scores.groupby("行业")["ESG"].mean().sort_values(ascending=False).reset_index()
    fig2 = px.bar(ind_avg, x="行业", y="ESG", color="行业", color_discrete_map=COLORS,
                  title="行业ESG均值对比", text=ind_avg["ESG"].apply(lambda x: f"{x:.3f}"))
    fig2.update_traces(textposition="outside")
    fig2.update_layout(showlegend=False, height=400, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(fig2.to_html(full_html=False, include_plotlyjs=False))

    # 3) E/S/G radar for top companies
    radar_data = scores.head(6)
    fig3 = go.Figure()
    for _, row in radar_data.iterrows():
        fig3.add_trace(go.Scatterpolar(
            r=[row["E"], row["S"], row["G"], row["E"]],
            theta=["环境(E)", "社会(S)", "治理(G)", "环境(E)"],
            name=row["公司"], fill="toself", opacity=0.5,
        ))
    fig3.update_layout(title="TOP6 ESG维度雷达图", height=450, polar=dict(radialaxis=dict(range=[0, 1.1])),
                       margin=dict(l=20, r=20, t=40, b=20))
    charts.append(fig3.to_html(full_html=False, include_plotlyjs=False))

    # 4) Industry company count pie
    ind_count = scores.groupby("行业").size().sort_values(ascending=False)
    fig4 = px.pie(values=ind_count.values, names=ind_count.index, color=ind_count.index,
                  color_discrete_map=COLORS, title=f"行业分布（共{companies_n}家公司）")
    fig4.update_traces(textinfo="label+value")
    fig4.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(fig4.to_html(full_html=False, include_plotlyjs=False))

    # 5) Carbon emissions by industry
    ghg = df[df["指标ID"] == "E_Q01"].groupby("行业")["数值"].mean().sort_values(ascending=False)
    if len(ghg) > 0:
        fig5 = px.bar(x=ghg.index, y=ghg.values, color=ghg.index,
                      color_discrete_map=COLORS, title="各行业平均碳排放（吨CO2e）",
                      labels={"x": "行业", "y": "碳排放(吨)"})
        fig5.update_layout(showlegend=False, height=350, margin=dict(l=20, r=20, t=40, b=20))
        charts.append(fig5.to_html(full_html=False, include_plotlyjs=False))

    # 6) Distribution: quality score histogram
    quality_scores = df.groupby("公司")["质量分"].mean()
    fig6 = px.histogram(quality_scores, nbins=30, title="报告质量分分布",
                        labels={"value": "质量分", "count": "公司数"})
    fig6.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    charts.append(fig6.to_html(full_html=False, include_plotlyjs=False))

    # 7) Key indicator averages by industry table
    ind_table = []
    for ind_name, grp in df.groupby("行业"):
        row_data = {"行业": ind_name, "公司数": grp["公司"].nunique()}
        for ind_id, lbl in [("E_Q01", "碳排放(吨)"), ("E_Q06", "可再生(%)"),
                            ("S_Q02", "女性员工(%)"), ("S_Q08", "研发占比(%)")]:
            vals = grp[grp["指标ID"] == ind_id]["数值"]
            if len(vals) > 0:
                row_data[lbl] = f"{vals.mean():,.1f}" if ind_id == "E_Q01" else f"{vals.mean():.1f}"
            else:
                row_data[lbl] = "-"
        ind_table.append(row_data)
    ind_df = pd.DataFrame(ind_table)

    # 8) Top 10 renewable energy companies
    renewable = df[df["指标ID"] == "E_Q06"].nlargest(10, "数值")[["公司", "行业", "数值"]]
    renewable.columns = ["公司", "行业", "可再生能源比例(%)"]

    # 9) Top 10 R&D companies
    rd = df[df["指标ID"] == "S_Q08"].nlargest(10, "数值")[["公司", "行业", "数值"]]
    rd.columns = ["公司", "行业", "研发投入占比(%)"]

    # 10) Score distribution table
    score_table = scores.head(30).copy()
    for c in ["E", "S", "G", "ESG"]:
        score_table[c] = score_table[c].apply(lambda x: f"{x:.3f}")

    # ===== Build HTML =====
    toc = ""
    for section_id, label in [
        ("overview", "📊 数据概览"),
        ("top20", "🏆 ESG排名"),
        ("industry", "🏭 行业对比"),
        ("details", "📋 指标详览"),
        ("quality", "✅ 数据质量"),
    ]:
        toc += f'<li><a href="#{section_id}">{label}</a></li>'

    sections = ""

    # Overview
    sections += f'''
    <section id="overview">
    <h2>📊 数据概览</h2>
    <div class="kpi-grid">
        <div class="kpi"><div class="num">{companies_n}</div><div class="label">覆盖公司</div></div>
        <div class="kpi"><div class="num">117</div><div class="label">ESG报告</div></div>
        <div class="kpi"><div class="num">{industries_n}</div><div class="label">行业</div></div>
        <div class="kpi"><div class="num">{len(df)}</div><div class="label">定量数据点</div></div>
        <div class="kpi"><div class="num">{quality_scores.mean():.3f}</div><div class="label">平均质量分</div></div>
        <div class="kpi"><div class="num">{df.groupby('公司')['覆盖度'].mean().mean():.1f}%</div><div class="label">平均覆盖度</div></div>
    </div>
    <div class="chart">{charts[5]}</div>
    <div class="chart">{charts[3]}</div>
    </section>
    '''

    # Top 20
    sections += f'''
    <section id="top20">
    <h2>🏆 ESG综合排名</h2>
    <div class="chart-row">
        <div class="chart chart-wide">{charts[0]}</div>
    </div>
    <div class="chart-row">
        <div class="chart chart-wide">{charts[2]}</div>
    </div>
    <div class="table-container">{score_table.to_html(classes="styled-table", border=0)}</div>
    </section>
    '''

    # Industry
    sections += f'''
    <section id="industry">
    <h2>🏭 行业对比</h2>
    <div class="chart-row">
        <div class="chart">{charts[1]}</div>
        <div class="chart">{charts[4] if len(charts) > 4 else ""}</div>
    </div>
    <h3>行业指标汇总</h3>
    <div class="table-container">{ind_df.to_html(classes="styled-table", border=0, index=False)}</div>
    </section>
    '''

    # Details
    sections += f'''
    <section id="details">
    <h2>📋 指标详览</h2>
    <div class="chart-row">
        <div class="chart">
            <h3>可再生能源比例 TOP10 (%)</h3>
            <div class="table-container">{renewable.to_html(classes="styled-table", border=0, index=False)}</div>
        </div>
        <div class="chart">
            <h3>研发投入占比 TOP10 (%)</h3>
            <div class="table-container">{rd.to_html(classes="styled-table", border=0, index=False)}</div>
        </div>
    </div>
    <h3>完整数据表（前200行）</h3>
    <div class="table-container" style="max-height:500px;overflow-y:auto;">{df.head(200).to_html(classes="styled-table", border=0, index=False)}</div>
    </section>
    '''

    # Quality
    quality_df = df.groupby("公司").agg(
        质量分=("质量分", "mean"),
        覆盖度=("覆盖度", "mean"),
        指标数=("数值", "count"),
    ).sort_values("质量分", ascending=False)
    for c in ["质量分", "覆盖度"]:
        quality_df[c] = quality_df[c].apply(lambda x: f"{x:.3f}")

    sections += f'''
    <section id="quality">
    <h2>✅ 数据质量</h2>
    <div class="table-container">{quality_df.head(30).to_html(classes="styled-table", border=0)}</div>
    </section>
    '''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESG数据智能提取与分析报告</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #f5f7fa; color: #333; }}
header {{ background: linear-gradient(135deg, #1a5276 0%, #2e86c1 100%); color: white; padding: 30px 0; text-align: center; }}
header h1 {{ font-size: 2em; margin-bottom: 8px; }}
header p {{ opacity: 0.85; }}
nav {{ background: white; padding: 12px 0; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
nav ul {{ list-style: none; display: flex; justify-content: center; gap: 30px; max-width: 1200px; margin: 0 auto; }}
nav a {{ text-decoration: none; color: #555; font-weight: 500; padding: 6px 12px; border-radius: 4px; transition: 0.2s; }}
nav a:hover {{ background: #e8f0fe; color: #1a5276; }}
.container {{ max-width: 1300px; margin: 0 auto; padding: 20px; }}
section {{ margin-bottom: 40px; }}
section h2 {{ font-size: 1.5em; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 3px solid #2e86c1; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.kpi {{ background: white; padding: 24px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.kpi .num {{ font-size: 2em; font-weight: 700; color: #1a5276; }}
.kpi .label {{ font-size: 0.9em; color: #888; margin-top: 4px; }}
.chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
@media (max-width: 900px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}
.chart {{ background: white; padding: 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
.chart-wide {{ grid-column: 1 / -1; }}
.chart h3 {{ margin-bottom: 8px; color: #555; }}
.table-container {{ background: white; padding: 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); overflow-x: auto; margin-bottom: 16px; }}
.styled-table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
.styled-table th {{ background: #1a5276; color: white; padding: 10px 12px; text-align: left; position: sticky; top: 0; }}
.styled-table td {{ padding: 8px 12px; border-bottom: 1px solid #eee; }}
.styled-table tr:hover {{ background: #f0f6ff; }}
footer {{ text-align: center; padding: 20px; color: #999; font-size: 0.85em; }}
</style>
</head>
<body>
<header>
    <h1>📊 ESG数据智能提取与分析报告</h1>
    <p>基于DeepSeek大模型 · A股上市公司ESG报告自动提取 · 数据要素大赛</p>
</header>
<nav><ul>{toc}</ul></nav>
<div class="container">{sections}</div>
<footer>© 2025 ESG Analysis · 数据覆盖{companies_n}家A股上市公司</footer>
</body>
</html>'''

    REPORT_PATH.write_text(html, encoding="utf-8")
    print(f"Report saved: {REPORT_PATH} ({REPORT_PATH.stat().st_size / 1024:.0f} KB)")
    return str(REPORT_PATH)


if __name__ == "__main__":
    generate()
