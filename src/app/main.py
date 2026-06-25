"""ESG数据智能提取与分析系统 - Streamlit主应用"""

import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.extractor.indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION

# 指标ID → 名称映射，用于数据库加载时补全指标名称
INDICATOR_MAP = {i.id: i for i in ALL_INDICATORS}

st.set_page_config(
    page_title="ESG数据智能提取与分析系统",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
ASSET_DIR = BASE_DIR / "src" / "app" / "assets"

# ---- 全局Plotly中文字体配置 ----
# Plotly在浏览器端渲染，字体必须在客户端存在。优先级：Windows > Mac > Linux
import plotly.io as pio
import plotly.graph_objects as go
_chinese_font = "Microsoft YaHei, PingFang SC, WenQuanYi Micro Hei, Noto Sans CJK SC, SimHei, sans-serif"
_font_template = go.layout.Template()
_font_template.layout.font.family = _chinese_font
_font_template.layout.title.font.family = _chinese_font
_font_template.layout.xaxis.title.font.family = _chinese_font
_font_template.layout.xaxis.tickfont.family = _chinese_font
_font_template.layout.yaxis.title.font.family = _chinese_font
_font_template.layout.yaxis.tickfont.family = _chinese_font
_font_template.layout.legend.font.family = _chinese_font
_font_template.layout.coloraxis.colorbar.title.font.family = _chinese_font
_font_template.layout.coloraxis.colorbar.tickfont.family = _chinese_font
_font_template.layout.paper_bgcolor = "rgba(0,0,0,0)"
_font_template.layout.plot_bgcolor = "rgba(255,255,255,0.55)"
_font_template.layout.colorway = [
    "#1f7a5c", "#2f6fbd", "#e0a43a", "#8f63d7", "#2f9fa7",
    "#d65f5f", "#6b8e23", "#4c78a8", "#f58518", "#54a24b",
]
_font_template.layout.margin = dict(l=24, r=24, t=56, b=36)
_font_template.layout.xaxis.gridcolor = "rgba(33, 71, 98, 0.10)"
_font_template.layout.yaxis.gridcolor = "rgba(33, 71, 98, 0.10)"
_font_template.layout.xaxis.zerolinecolor = "rgba(33, 71, 98, 0.14)"
_font_template.layout.yaxis.zerolinecolor = "rgba(33, 71, 98, 0.14)"
if "esg_chinese" not in pio.templates:
    pio.templates["esg_chinese"] = _font_template
pio.templates.default = "esg_chinese"


def asset_data_uri(filename: str) -> str:
    """将项目内图片转成data URI，便于Streamlit Cloud稳定展示。"""
    path = ASSET_DIR / filename
    if not path.exists():
        return ""
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def inject_global_styles() -> None:
    hero_uri = asset_data_uri("esg-hero.png")
    empty_uri = asset_data_uri("esg-empty-state.png")
    st.markdown(
        f"""
        <style>
        :root {{
            --ink: #143042;
            --muted: #617282;
            --line: rgba(25, 55, 76, 0.10);
            --surface: rgba(255, 255, 255, 0.74);
            --surface-strong: rgba(255, 255, 255, 0.92);
            --green: #1f7a5c;
            --blue: #2f6fbd;
            --gold: #d99b2b;
        }}
        .stApp {{
            background:
                radial-gradient(circle at 9% 8%, rgba(38, 166, 124, .18), transparent 26rem),
                radial-gradient(circle at 86% 12%, rgba(62, 110, 196, .16), transparent 30rem),
                linear-gradient(135deg, #f8fbf8 0%, #f6fbff 45%, #eef6f0 100%);
            color: var(--ink);
        }}
        [data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(14, 45, 58, .96), rgba(18, 78, 70, .92)),
                radial-gradient(circle at 50% 0%, rgba(99, 199, 145, .25), transparent 18rem);
        }}
        [data-testid="stSidebar"] * {{
            color: rgba(255, 255, 255, .90);
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
            border-radius: 14px;
            padding: .28rem .42rem;
            margin: .12rem 0;
            transition: all .18s ease;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba(255, 255, 255, .10);
        }}
        .block-container {{
            padding-top: 1.15rem;
            max-width: 1420px;
        }}
        div[data-testid="stMetric"], div[data-testid="stPlotlyChart"] {{
            background: rgba(255,255,255,.72);
            border: 1px solid rgba(255,255,255,.84);
            border-radius: 18px;
            padding: .65rem;
            box-shadow: 0 18px 46px rgba(20, 48, 66, .08);
        }}
        .brand-card {{
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 20px;
            padding: 1rem;
            background: rgba(255,255,255,.10);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18);
        }}
        .brand-title {{
            font-size: 1.05rem;
            font-weight: 800;
            line-height: 1.28;
            margin-bottom: .35rem;
        }}
        .brand-subtitle {{
            color: rgba(255,255,255,.68) !important;
            font-size: .82rem;
            line-height: 1.55;
        }}
        .hero-shell {{
            position: relative;
            overflow: hidden;
            min-height: 310px;
            border: 1px solid rgba(255, 255, 255, .86);
            border-radius: 28px;
            padding: 2.15rem 2.35rem;
            margin-bottom: 1.25rem;
            background-image:
                linear-gradient(90deg, rgba(7, 32, 44, .78), rgba(7, 32, 44, .28) 52%, rgba(7, 32, 44, .05)),
                url("{hero_uri}");
            background-size: cover;
            background-position: center;
            box-shadow: 0 28px 72px rgba(27, 72, 86, .18);
        }}
        .hero-eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .34rem .68rem;
            border: 1px solid rgba(255, 255, 255, .35);
            border-radius: 999px;
            background: rgba(255, 255, 255, .16);
            color: rgba(255, 255, 255, .92);
            font-size: .86rem;
            backdrop-filter: blur(8px);
        }}
        .hero-title {{
            max-width: 760px;
            margin: 1.1rem 0 .65rem;
            color: #ffffff;
            font-size: clamp(2.1rem, 4vw, 4rem);
            line-height: 1.04;
            font-weight: 850;
            letter-spacing: 0;
        }}
        .hero-subtitle {{
            max-width: 700px;
            color: rgba(255, 255, 255, .83);
            font-size: 1.05rem;
            line-height: 1.8;
        }}
        .hero-actions {{
            display: flex;
            flex-wrap: wrap;
            gap: .65rem;
            margin-top: 1.4rem;
        }}
        .pill {{
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            padding: .5rem .74rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, .32);
            background: rgba(255, 255, 255, .14);
            color: rgba(255, 255, 255, .92);
            font-size: .9rem;
            backdrop-filter: blur(8px);
        }}
        .metric-card {{
            position: relative;
            overflow: hidden;
            min-height: 132px;
            padding: 1rem 1.05rem;
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, .88);
            background: linear-gradient(145deg, rgba(255,255,255,.94), rgba(255,255,255,.68));
            box-shadow: 0 18px 46px rgba(20, 48, 66, .08);
        }}
        .metric-card:after {{
            content: "";
            position: absolute;
            right: -34px;
            top: -38px;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: var(--accent);
            opacity: .18;
        }}
        .metric-kicker {{
            color: var(--muted);
            font-size: .84rem;
            margin-bottom: .34rem;
        }}
        .metric-value {{
            color: var(--ink);
            font-size: 1.92rem;
            line-height: 1.05;
            font-weight: 820;
            letter-spacing: 0;
        }}
        .metric-note {{
            color: var(--muted);
            font-size: .82rem;
            margin-top: .52rem;
        }}
        .section-title {{
            display: flex;
            align-items: center;
            gap: .62rem;
            margin: 1.2rem 0 .8rem;
        }}
        .section-dot {{
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--green), var(--gold));
            box-shadow: 0 0 0 7px rgba(31, 122, 92, .10);
        }}
        .section-title h3 {{
            margin: 0;
            font-size: 1.18rem;
            color: var(--ink);
            letter-spacing: 0;
        }}
        .dimension-card {{
            border: 1px solid rgba(255,255,255,.88);
            border-radius: 18px;
            padding: 1rem 1.05rem;
            margin-bottom: .75rem;
            background: linear-gradient(145deg, rgba(255,255,255,.90), rgba(255,255,255,.64));
            box-shadow: 0 16px 42px rgba(20, 48, 66, .07);
        }}
        .dimension-topline {{
            display: flex;
            align-items: center;
            gap: .55rem;
            color: var(--ink);
            font-weight: 780;
            margin-bottom: .55rem;
        }}
        .dimension-swatch {{
            width: 12px;
            height: 12px;
            border-radius: 999px;
            background: var(--dim-color);
            box-shadow: 0 0 0 7px color-mix(in srgb, var(--dim-color) 16%, transparent);
        }}
        .dimension-counts {{
            display: flex;
            gap: .55rem;
            flex-wrap: wrap;
        }}
        .dimension-chip {{
            border: 1px solid rgba(20, 48, 66, .08);
            border-radius: 999px;
            padding: .28rem .55rem;
            background: rgba(255,255,255,.70);
            color: var(--muted);
            font-size: .82rem;
        }}
        .empty-state {{
            display: grid;
            grid-template-columns: minmax(180px, 260px) 1fr;
            gap: 1.4rem;
            align-items: center;
            border: 1px solid rgba(255, 255, 255, .86);
            border-radius: 24px;
            padding: 1.35rem;
            background: rgba(255, 255, 255, .72);
            box-shadow: 0 18px 46px rgba(20, 48, 66, .08);
        }}
        .empty-state img {{
            width: 100%;
            max-width: 240px;
            border-radius: 20px;
            box-shadow: 0 18px 44px rgba(20, 48, 66, .12);
        }}
        .empty-state h3 {{
            margin: 0 0 .35rem;
            color: var(--ink);
        }}
        .empty-state p {{
            margin: 0;
            color: var(--muted);
            line-height: 1.75;
        }}
        @media (max-width: 760px) {{
            .hero-shell {{ padding: 1.45rem; min-height: 360px; }}
            .hero-title {{ font-size: 2.2rem; }}
            .empty-state {{ grid-template-columns: 1fr; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: str, note: str = "", accent: str = "#1f7a5c") -> None:
    st.markdown(
        f"""
        <div class="metric-card" style="--accent:{accent}">
            <div class="metric-kicker">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">
            <span class="section-dot"></span>
            <h3>{title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dimension_summary(dim_name: str, qt_count: int, ql_count: int, color: str) -> None:
    st.markdown(
        f"""
        <div class="dimension-card" style="--dim-color:{color}">
            <div class="dimension-topline"><span class="dimension-swatch"></span>{dim_name}</div>
            <div class="dimension-counts">
                <span class="dimension-chip">定量 {qt_count}</span>
                <span class="dimension-chip">定性 {ql_count}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, body: str) -> None:
    empty_uri = asset_data_uri("esg-empty-state.png")
    st.markdown(
        f"""
        <div class="empty-state">
            <img src="{empty_uri}" alt="ESG数据可视化插图" />
            <div>
                <h3>{title}</h3>
                <p>{body}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def polish_fig(fig, title: str | None = None, height: int | None = None):
    """统一图表质感：留白、透明背景、坐标轴和hover样式。"""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.54)",
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=_chinese_font),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=24, r=24, t=56, b=36),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=15, color="#143042"))
    if height:
        layout["height"] = height
    fig.update_layout(**layout)
    try:
        fig.update_xaxes(showgrid=True, gridcolor="rgba(33, 71, 98, 0.10)", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="rgba(33, 71, 98, 0.10)", zeroline=False)
    except Exception:
        pass
    return fig


@st.cache_resource
def get_db():
    """延迟加载数据库（缓存连接）"""
    try:
        from src.utils.db import Database
        db_path = BASE_DIR / "data" / "esg_data.db"
        if db_path.exists():
            return Database(str(db_path))
    except Exception:
        pass
    return None


@st.cache_data
def load_all_results() -> list:
    """加载所有提取结果 — 优先数据库，回退JSON"""
    db = get_db()
    if db:
        try:
            stats = db.get_statistics()
            if stats["reports_done"] > 0:
                return _load_from_database(db)
        except Exception:
            pass

    return _load_from_json()


def _load_from_database(db) -> list:
    """从数据库加载提取结果"""
    results = []
    session = db.get_session()
    try:
        from src.utils.db import Company, Report, ExtractedValue, ExtractedText
        reports = session.query(Report).filter_by(extraction_status="done").all()
        for report in reports:
            result = {
                "company_name": report.company.name if report.company else "",
                "report_year": str(report.year),
                "quantitative_indicators": [],
                "qualitative_indicators": [],
                "validation": {
                    "overall_quality_score": report.quality_score or 0,
                    "quantitative_valid": sum(1 for v in report.values if v.value is not None),
                    "quantitative_count": len(report.values),
                    "qualitative_valid": sum(1 for t in report.texts if t.status),
                    "qualitative_count": len(report.texts),
                    "quantitative_issues": [],
                    "qualitative_issues": [],
                },
                "completeness": {
                    "total_indicators": 52,
                    "extracted": len(set(v.indicator_id for v in report.values) | set(t.indicator_id for t in report.texts)),
                    "missing": 0,
                    "completeness": report.completeness or 0,
                },
            }
            for v in report.values:
                ind_def = INDICATOR_MAP.get(v.indicator_id)
                result["quantitative_indicators"].append({
                    "id": v.indicator_id,
                    "name": ind_def.name if ind_def else v.indicator_id,
                    "value": v.value,
                    "unit": v.unit or (ind_def.unit if ind_def else ""),
                    "original_text": v.original_text,
                    "confidence": v.confidence,
                })
            for t in report.texts:
                ind_def = INDICATOR_MAP.get(t.indicator_id)
                result["qualitative_indicators"].append({
                    "id": t.indicator_id,
                    "name": ind_def.name if ind_def else t.indicator_id,
                    "status": t.status,
                    "summary": t.summary,
                    "original_text": t.original_text,
                    "confidence": t.confidence,
                })
            results.append(result)
    finally:
        session.close()
    return results


def _load_from_json() -> list:
    """从JSON文件加载提取结果"""
    results = []
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.glob("*_result.json")):
            with open(f, "r", encoding="utf-8") as fp:
                results.append(json.load(fp))
    return results


def build_dataframe(results: list) -> pd.DataFrame:
    """将提取结果转为DataFrame，自动补全缺失的指标名称"""
    rows = []
    for r in results:
        company = r.get("company_name", "")
        year = r.get("report_year", "")
        validation = r.get("validation", {})
        completeness = r.get("completeness", {})
        quality = validation.get("overall_quality_score", 0)
        coverage = completeness.get("completeness", 0)

        for item in r.get("quantitative_indicators", []):
            ind_id = item.get("id", "")
            name = item.get("name") or (INDICATOR_MAP[ind_id].name if ind_id in INDICATOR_MAP else ind_id)
            rows.append({
                "公司": company,
                "年份": year,
                "指标ID": ind_id,
                "指标名称": name,
                "数值": item.get("value"),
                "单位": item.get("unit"),
                "置信度": item.get("confidence"),
                "类型": "定量",
                "质量分": quality,
                "覆盖度": coverage,
            })
        for item in r.get("qualitative_indicators", []):
            ind_id = item.get("id", "")
            name = item.get("name") or (INDICATOR_MAP[ind_id].name if ind_id in INDICATOR_MAP else ind_id)
            rows.append({
                "公司": company,
                "年份": year,
                "指标ID": ind_id,
                "指标名称": name,
                "数值": item.get("status"),
                "单位": "",
                "置信度": item.get("confidence"),
                "类型": "定性",
                "质量分": quality,
                "覆盖度": coverage,
            })
    return pd.DataFrame(rows)


inject_global_styles()

# ====== 侧边栏导航 ======
NAV_LABELS = {
    "首页概览": "首页概览",
    "数据质量": "数据质量",
    "公司详情": "公司详情",
    "指标对比": "指标对比",
    "ESG分析": "ESG分析",
    "AI智能助手": "AI智能助手",
    "数据管理": "数据管理",
}

with st.sidebar:
    st.markdown(
        """
        <div class="brand-card">
            <div class="brand-title">ESG数据智能提取与分析系统</div>
            <div class="brand-subtitle">面向数据要素大赛的报告抽取、质量评估与可视化决策平台</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    page = st.radio(
        "导航",
        list(NAV_LABELS.keys()),
        format_func=lambda p: NAV_LABELS[p],
    )
    st.markdown("---")

    # 数据库状态
    db = get_db()
    if db:
        try:
            s = db.get_statistics()
            st.caption(f"数据库: {s['companies']}公司 | {s['reports_done']}报告已提取")
            denominator = max(s.get("reports", 0), 1)
            st.progress(min(s.get("reports_done", 0) / denominator, 1.0), text="提取进度")
        except Exception:
            st.caption("数据库: 未连接")
    else:
        st.caption("数据库: 未初始化（运行 db-import）")

    with st.expander("作品亮点", expanded=False):
        st.caption("52项E/S/G指标体系")
        st.caption("定量数值、单位、证据原文同步保留")
        st.caption("支持质量评估、公司对比、行业洞察和自然语言查询")

    st.caption("数据要素大赛 · ESG报告智能提取与分析")

# ====== 首页概览 ======
if page == "首页概览":
    results = load_all_results()
    df = build_dataframe(results) if results else pd.DataFrame()

    st.markdown(
        """
        <section class="hero-shell">
            <div class="hero-eyebrow">ESG Report Intelligence · Quant & Qual Extraction</div>
            <h1 class="hero-title">让上市公司ESG报告变成可验证的数据资产</h1>
            <div class="hero-subtitle">
                基于DeepSeek大模型、PDF表格解析和结构化校验，将冗长报告自动转化为指标、证据、质量分和交互式分析视图。
            </div>
            <div class="hero-actions">
                <span class="pill">E/S/G三维指标体系</span>
                <span class="pill">数值 + 单位 + 原文证据</span>
                <span class="pill">质量评估与可视化决策</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # KPI行
    report_count = len(results) or 0
    company_count = df["公司"].nunique() if not df.empty else 0
    quantitative_count = len([i for i in ALL_INDICATORS if i.indicator_type == "quantitative"])
    qualitative_count = len([i for i in ALL_INDICATORS if i.indicator_type == "qualitative"])
    if not df.empty and "质量分" in df.columns:
        avg_q = df.groupby("公司")["质量分"].mean().mean()
        avg_q_text = f"{avg_q:.2f}" if avg_q else "N/A"
    else:
        avg_q_text = "N/A"

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_metric_card("已处理报告", f"{report_count:,}", "JSON/数据库结果", "#1f7a5c")
    with col2:
        render_metric_card("覆盖公司", f"{company_count:,}", "上市公司样本", "#2f6fbd")
    with col3:
        render_metric_card("定量指标", str(quantitative_count), "数值、单位、上下文", "#d99b2b")
    with col4:
        render_metric_card("定性指标", str(qualitative_count), "政策、机制、战略", "#8f63d7")
    with col5:
        render_metric_card("平均质量分", avg_q_text, "完整性与合理性综合", "#2f9fa7")

    # 指标体系概览
    render_section("指标体系概览（共{}个指标）".format(len(ALL_INDICATORS)))
    col_e, col_s, col_g = st.columns(3)

    for col, dim, dim_name, color in [
        (col_e, "E", "环境 (Environmental)", "#2ecc71"),
        (col_s, "S", "社会 (Social)", "#3498db"),
        (col_g, "G", "治理 (Governance)", "#e74c3c"),
    ]:
        with col:
            indicators = INDICATORS_BY_DIMENSION.get(dim, [])
            qt_count = sum(1 for i in indicators if i.indicator_type == "quantitative")
            ql_count = sum(1 for i in indicators if i.indicator_type == "qualitative")
            render_dimension_summary(dim_name, qt_count, ql_count, color)
            with st.expander("查看指标列表"):
                for ind in indicators:
                    tag = "[定量]" if ind.indicator_type == "quantitative" else "[定性]"
                    st.caption(f"{tag} [{ind.id}] {ind.name}")

    # 数据预览
    if not df.empty:
        render_section("数据预览（前50行）")
        st.dataframe(df.head(50), use_container_width=True)

    # 行业统计（数据库可用时）
    db = get_db()
    if db:
        try:
            industry_stats = db.get_industry_stats()
            if industry_stats:
                render_section("行业覆盖分布")
                ind_df = pd.DataFrame(industry_stats)
                st.dataframe(ind_df, use_container_width=True)
        except Exception:
            pass

# ====== 数据质量页 ======
elif page == "数据质量":
    st.title("数据质量评估")

    results = load_all_results()
    if not results:
        render_empty_state("暂无可视化数据", "请先运行提取流水线或导入JSON/SQLite结果。系统会在数据就绪后自动生成质量评估、公司画像和指标对比视图。")
    else:
        # 质量分汇总
        quality_data = []
        for r in results:
            validation = r.get("validation", {})
            completeness = r.get("completeness", {})
            quality_data.append({
                "公司": r.get("company_name", ""),
                "年份": r.get("report_year", ""),
                "质量分": validation.get("overall_quality_score", 0),
                "覆盖度(%)": completeness.get("completeness", 0),
                "定量有效": validation.get("quantitative_valid", 0),
                "定量总数": validation.get("quantitative_count", 0),
                "定性有效": validation.get("qualitative_valid", 0),
                "定性总数": validation.get("qualitative_count", 0),
            })

        qdf = pd.DataFrame(quality_data)
        qdf = qdf.sort_values("质量分", ascending=False)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均质量分", f"{qdf['质量分'].mean():.3f}" if not qdf.empty else "N/A")
        with col2:
            st.metric("平均覆盖度", f"{qdf['覆盖度(%)'].mean():.1f}%" if not qdf.empty else "N/A")
        with col3:
            high_q = (qdf["质量分"] > 0.5).sum() if not qdf.empty else 0
            st.metric("高质量报告(>0.5)", high_q)

        st.markdown("---")
        render_section("各报告质量明细")
        st.dataframe(qdf, use_container_width=True, hide_index=True)

        # 质量分布图
        if not qdf.empty:
            st.markdown("---")
            render_section("质量分布")
            try:
                import plotly.graph_objects as go
                data = qdf["质量分"].dropna()
                counts, bin_edges = np.histogram(data, bins=25, range=(0, 1))
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                bin_width = bin_edges[1] - bin_edges[0]

                col_pie, col_bar = st.columns([1, 2])

                with col_pie:
                    # 质量等级环形图
                    def classify(v):
                        if v >= 0.7: return "优秀"
                        elif v >= 0.4: return "良好"
                        else: return "待改进"
                    tier_map = {"优秀": 0, "良好": 0, "待改进": 0}
                    for v in data:
                        tier_map[classify(v)] += 1
                    tier_labels = ["优秀 (>=0.7)", "良好 (0.4~0.7)", "待改进 (<0.4)"]
                    tier_vals = [tier_map["优秀"], tier_map["良好"], tier_map["待改进"]]
                    tier_colors = ["#1a237e", "#42a5f5", "#bbdefb"]

                    fig_pie = go.Figure(go.Pie(
                        labels=tier_labels, values=tier_vals,
                        marker=dict(colors=tier_colors, line=dict(color="white", width=2)),
                        hole=0.5, textinfo="label+percent",
                        textfont=dict(size=12),
                        sort=False,
                    ))
                    fig_pie.update_layout(
                        title=dict(text="质量等级", font=dict(size=14)),
                        height=320, margin=dict(l=10, r=10, t=40, b=10),
                        showlegend=False,
                    )
                    st.plotly_chart(polish_fig(fig_pie), use_container_width=True)

                with col_bar:
                    # 蓝靛渐变直方图
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=bin_centers, y=counts, width=bin_width * 0.92,
                        marker=dict(
                            color=bin_centers,
                            colorscale=[[0, "#e8eaf6"], [0.3, "#7986cb"], [0.6, "#3949ab"], [1, "#1a237e"]],
                            showscale=False,
                            line=dict(color="white", width=0.5),
                        ),
                        hovertemplate="质量分: %{x:.2f}<br>报告数: %{y}<extra></extra>",
                    ))
                    avg_q = data.mean()
                    fig.add_vline(
                        x=avg_q, line_dash="dash", line_color="#d32f2f",
                        line_width=2, annotation_text=f"均值 {avg_q:.3f}",
                        annotation_position="top right",
                        annotation_font=dict(color="#d32f2f", size=12),
                    )
                    fig.update_layout(
                        title=dict(text="报告质量分分布", font=dict(size=14)),
                        height=320, margin=dict(l=10, r=10, t=40, b=10),
                        xaxis=dict(title="质量分", range=[0, 1.05]),
                        yaxis=dict(title="报告数量"),
                        plot_bgcolor="rgba(0,0,0,0)", bargap=0.05,
                    )
                    st.plotly_chart(polish_fig(fig), use_container_width=True)
            except ImportError:
                st.bar_chart(qdf.set_index("公司")["质量分"])

        # 问题详情
        st.markdown("---")
        render_section("校验问题详情")
        selected_company = st.selectbox("选择公司查看问题", qdf["公司"].tolist())
        company_result = next(
            (r for r in results if r.get("company_name") == selected_company), None
        )
        if company_result:
            validation = company_result.get("validation", {})
            qt_issues = validation.get("quantitative_issues", [])
            ql_issues = validation.get("qualitative_issues", [])

            if qt_issues:
                st.markdown("**定量指标问题:**")
                st.dataframe(pd.DataFrame(qt_issues), use_container_width=True)
            else:
                st.success("定量指标无不合理值")

            if ql_issues:
                st.markdown("**定性指标问题:**")
                st.dataframe(pd.DataFrame(ql_issues), use_container_width=True)
            else:
                st.success("定性指标无问题")

            completeness = company_result.get("completeness", {})
            missing = completeness.get("missing_list", [])
            if missing:
                st.markdown("**未覆盖的指标:**")
                st.dataframe(pd.DataFrame(missing), use_container_width=True)

# ====== 公司详情页 ======
elif page == "公司详情":
    st.title("公司ESG详情查询")

    results = load_all_results()
    if not results:
        render_empty_state("暂无可视化数据", "请先运行提取流水线或导入JSON/SQLite结果。系统会在数据就绪后自动生成质量评估、公司画像和指标对比视图。")
    else:
        companies = sorted(set(r.get("company_name", "") for r in results))
        selected = st.selectbox("选择公司", companies)

        company_result = next(
            (r for r in results if r.get("company_name") == selected), None
        )
        if company_result:
            year = company_result.get("report_year", "")
            validation = company_result.get("validation", {})
            completeness = company_result.get("completeness", {})

            render_section(f"{selected} — {year}年度ESG报告")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("质量分", f"{validation.get('overall_quality_score', 0):.3f}")
            with col2:
                st.metric("指标覆盖度", f"{completeness.get('completeness', 0)}%")
            with col3:
                qt = validation.get("quantitative_valid", 0)
                ql = validation.get("qualitative_valid", 0)
                st.metric("有效指标", f"{qt}定量 + {ql}定性")

            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["环境 (E)", "社会 (S)", "治理 (G)"])

            for tab, dim in [(tab1, "E"), (tab2, "S"), (tab3, "G")]:
                with tab:
                    dim_indicators = {i.id: i for i in INDICATORS_BY_DIMENSION.get(dim, [])}

                    # 定量指标
                    qt = [
                        item for item in company_result.get("quantitative_indicators", [])
                        if item.get("id") in dim_indicators
                    ]
                    if qt:
                        st.markdown("**定量指标**")
                        qt_data = []
                        for item in qt:
                            ind_def = dim_indicators.get(item.get("id", ""))
                            qt_data.append({
                                "指标": ind_def.name if ind_def else item.get("name", ""),
                                "数值": item.get("value"),
                                "单位": item.get("unit"),
                                "置信度": item.get("confidence", ""),
                                "原文": (item.get("original_text") or "")[:100],
                            })
                        st.dataframe(pd.DataFrame(qt_data), use_container_width=True)
                    else:
                        st.caption("暂无定量指标数据")

                    # 定性指标
                    ql = [
                        item for item in company_result.get("qualitative_indicators", [])
                        if item.get("id") in dim_indicators
                    ]
                    if ql:
                        st.markdown("**定性指标**")
                        for item in ql:
                            status_label = {"yes": "[是]", "no": "[否]", "partial": "[部分]"}.get(
                                item.get("status"), "[未知]"
                            )
                            ind_def = dim_indicators.get(item.get("id", ""))
                            label = ind_def.name if ind_def else item.get("name", "")
                            with st.expander(f"{status_label} {label}"):
                                st.write(item.get("summary", "无描述"))
                                if item.get("original_text"):
                                    st.caption(f"原文: {item['original_text'][:200]}")
                    else:
                        st.caption("暂无定性指标数据")

# ====== 指标对比页 ======
elif page == "指标对比":
    st.title("多公司ESG指标对比")

    results = load_all_results()
    if not results:
        render_empty_state("暂无可视化数据", "请先运行提取流水线或导入JSON/SQLite结果。系统会在数据就绪后自动生成质量评估、公司画像和指标对比视图。")
    else:
        df = build_dataframe(results)

        # 只保留定量指标（定性指标为文本判断，不适合数值对比）
        qt_df = df[df["类型"] == "定量"] if not df.empty else df

        if qt_df.empty:
            render_empty_state("暂无定量指标", "当前结果中没有可用于横向对比的数值型指标。建议先检查抽取结果、字段单位和质量校验状态。")
        else:
            # 维度筛选
            dim_filter = st.radio("筛选维度", ["全部", "E-环境", "S-社会", "G-治理"], horizontal=True)
            dim_map = {"E-环境": "E", "S-社会": "S", "G-治理": "G"}
            if dim_filter != "全部":
                dim_ids = {i.id for i in INDICATORS_BY_DIMENSION.get(dim_map[dim_filter], [])}
                qt_df = qt_df[qt_df["指标ID"].isin(dim_ids)]

            if qt_df.empty:
                render_empty_state("该维度暂无数据", "可以切换到其他E/S/G维度，或在完成新数据抽取后返回查看。")
            else:
                # 按指标ID分组，构建 (ID, 名称, 单位, 有数据的公司数) 的选项列表
                indicator_options = []
                for ind_id, group in qt_df.groupby("指标ID"):
                    name = group["指标名称"].iloc[0] if not group.empty else ind_id
                    unit = group["单位"].iloc[0] if not group.empty else ""
                    has_data = group["数值"].notna().sum()
                    label = f"[{ind_id}] {name} ({unit})" if unit else f"[{ind_id}] {name}"
                    indicator_options.append({
                        "label": label,
                        "id": ind_id,
                        "name": name,
                        "unit": unit,
                        "count": has_data,
                    })

                # 按指标ID排序
                indicator_options.sort(key=lambda x: x["id"])

                # 构建selectbox的标签列表
                option_labels = [
                    f"{opt['label']} — {opt['count']}家公司有数据"
                    for opt in indicator_options
                ]

                selected_label = st.selectbox("选择对比指标", option_labels)
                selected_idx = option_labels.index(selected_label)
                selected = indicator_options[selected_idx]

                # 显示指标详情
                ind_def = INDICATOR_MAP.get(selected["id"])
                if ind_def:
                    st.caption(f"指标说明：{ind_def.description}")

                st.markdown("---")

                # 按指标ID过滤（更精确）
                indicator_data = qt_df[qt_df["指标ID"] == selected["id"]].copy()

                # 只保留有数值的行
                indicator_data = indicator_data[indicator_data["数值"].notna()]

                if indicator_data.empty:
                    st.info(f"「{selected['name']}」所有公司均无数据。")
                else:
                    render_section(f"{selected['name']} — 各公司对比")

                    # 表格：显示指标名称+数值+单位+年份+置信度
                    display_df = indicator_data[
                        ["公司", "年份", "数值", "单位", "置信度"]
                    ].copy()
                    display_df = display_df.sort_values("数值", ascending=False)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

                    # 水平柱状图
                    try:
                        import plotly.graph_objects as go

                        # 同一公司取最大数值去重，避免多年数据导致的标签重叠
                        chart_data = (
                            indicator_data
                            .sort_values("数值", ascending=False)
                            .groupby("公司", as_index=False)
                            .first()
                            .sort_values("数值", ascending=True)
                            .tail(20)
                        )

                        if len(chart_data) == 0:
                            st.info("无有效数据可展示。")
                        else:
                            max_val = chart_data["数值"].max()
                            # 根据数值量级动态计算padding，确保标签不溢出
                            if max_val > 0:
                                log10 = max(0, np.log10(max_val))
                                padding = 1.2 + min(log10 * 0.08, 0.35)  # 大数值加更多padding
                                x_max = max_val * padding
                            else:
                                x_max = 1
                            unit = selected.get("unit", "")

                            def fmt(v):
                                try:
                                    if abs(v) >= 1e9:
                                        return f"{v/1e9:,.2f}B"
                                    elif abs(v) >= 1e6:
                                        return f"{v/1e6:,.2f}M"
                                    elif abs(v) >= 1e4:
                                        return f"{v:,.0f}"
                                    elif abs(v) >= 100:
                                        return f"{v:,.2f}"
                                    elif abs(v) < 0.01:
                                        return f"{v:.4f}"
                                    else:
                                        return f"{v:.2f}"
                                except Exception:
                                    return str(v)

                            fig = go.Figure()
                            fig.add_trace(go.Bar(
                                y=chart_data["公司"], x=chart_data["数值"],
                                orientation="h",
                                marker=dict(
                                    color=chart_data["数值"],
                                    colorscale=[[0, "#e8eaf6"], [0.3, "#7986cb"], [0.6, "#3949ab"], [1, "#1a237e"]],
                                    showscale=True,
                                    colorbar=dict(title=unit, thickness=12, len=0.5),
                                    line=dict(width=0),
                                ),
                                text=chart_data["数值"].apply(fmt),
                                textposition="outside",
                                textfont=dict(size=12),
                                cliponaxis=False,
                                hovertemplate="%{y}: %{x:,.2f} " + unit + "<extra></extra>",
                            ))
                            fig.update_layout(
                                title=dict(text=f"{selected['name']} 各公司对比 TOP20", font=dict(size=14)),
                                height=max(400, 35 + len(chart_data) * 32),
                                margin=dict(l=10, r=80, t=40, b=10),
                                xaxis=dict(title=f"{selected['name']} ({unit})" if unit else selected['name'], range=[0, x_max]),
                                yaxis=dict(title="", autorange="reversed", tickfont=dict(size=12)),
                                plot_bgcolor="rgba(0,0,0,0)",
                                showlegend=False,
                            )
                            st.plotly_chart(polish_fig(fig), use_container_width=True)
                    except ImportError:
                        st.bar_chart(indicator_data.set_index("公司")["数值"])

# ====== ESG分析页 ======
elif page == "ESG分析":
    st.title("ESG综合分析")

    try:
        from src.analyzer import load_clean_data, compute_esg_scores, industry_analysis, generate_insights

        with st.spinner("计算ESG评分..."):
            df = load_clean_data()
            scores = compute_esg_scores(df)
            industries = industry_analysis(df)
            insights = generate_insights(df)

        # ESG排名
        render_section("ESG综合排名 TOP20")
        col1, col2 = st.columns([5, 4])
        with col1:
            st.dataframe(scores.head(20), use_container_width=True, hide_index=True)
        with col2:
            if not scores.empty:
                try:
                    import plotly.graph_objects as go
                    top10 = scores.head(10).iloc[::-1]
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=top10["公司"], x=top10["ESG综合"],
                        orientation="h",
                        marker=dict(
                            color=top10["ESG综合"],
                            colorscale="blugrn",
                            showscale=True,
                            colorbar=dict(title="得分", thickness=12, len=0.5),
                        ),
                        text=top10["ESG综合"].apply(lambda v: f"{v:.3f}"),
                        textposition="outside",
                        hovertemplate="%{y}: %{x:.3f}<extra></extra>",
                    ))
                    fig.update_layout(
                        title=dict(text="ESG综合得分 TOP10", font=dict(size=14)),
                        height=400, margin=dict(l=10, r=10, t=40, b=10),
                        xaxis=dict(range=[0, 1.15], title="ESG综合得分"),
                        yaxis=dict(title=""),
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(polish_fig(fig), use_container_width=True)
                except ImportError:
                    st.bar_chart(top10.set_index("公司")["ESG综合"])

        # ESG维度分布
        st.markdown("---")
        render_section("E/S/G 维度得分分布")

        dim_configs = [
            ("E_得分", "环境 (E)", "#2e7d32"),
            ("S_得分", "社会 (S)", "#1565c0"),
            ("G_得分", "治理 (G)", "#e65100"),
        ]

        for dim, label, accent in dim_configs:
            avg = scores[dim].mean()
            st.metric(f"{label} 均值", f"{avg:.3f}")

            try:
                import plotly.graph_objects as go
                data = scores[dim].dropna()

                counts, bin_edges = np.histogram(data, bins=28, range=(0, 1))
                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                bin_width = bin_edges[1] - bin_edges[0]

                # 3D立体柱状图
                fig = go.Figure(go.Bar3d(
                    x=bin_centers,
                    y=[0] * len(bin_centers),
                    z=counts,
                    dx=bin_width * 0.82,
                    dy=0.12,
                    marker=dict(
                        color=counts,
                        colorscale=[[0, "#fafafa"], [0.35, accent], [1, accent]],
                        line=dict(color="rgba(255,255,255,0.7)", width=1),
                        colorbar=dict(title="公司数", len=0.5, x=1.02),
                    ),
                    hovertemplate="得分区间: %{x:.2f}<br>公司数: %{z}<extra></extra>",
                ))

                # 均值参考线
                fig.add_trace(go.Scatter3d(
                    x=[avg, avg], y=[0, 0], z=[0, max(counts) * 1.15],
                    mode="lines",
                    line=dict(color="#d32f2f", width=4),
                    name=f"均值 {avg:.3f}",
                    hovertemplate="均值: %{x:.3f}<extra></extra>",
                ))

                fig.update_layout(
                    title=dict(text=f"{label}得分分布", font=dict(size=14)),
                    height=420,
                    scene=dict(
                        xaxis=dict(title="得分", range=[0, 1.05]),
                        yaxis=dict(showticklabels=False, title="", range=[-0.15, 0.25]),
                        zaxis=dict(title="公司数量"),
                        camera=dict(eye=dict(x=1.6, y=1.6, z=1.1)),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    margin=dict(l=10, r=10, t=40, b=10),
                )
                st.plotly_chart(polish_fig(fig), use_container_width=True)
            except Exception:
                pass
            st.markdown("<br style='line-height:2rem;'>", unsafe_allow_html=True)

        # 行业对比
        st.markdown("---")
        render_section("行业ESG对比")
        if not industries.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                st.dataframe(industries, use_container_width=True, hide_index=True)
            with col_b:
                ind_valid = industries.dropna(subset=["平均碳排放(吨)"])
                if not ind_valid.empty:
                    try:
                        import plotly.graph_objects as go
                        ind_valid = ind_valid.sort_values("平均碳排放(吨)", ascending=True)
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            y=ind_valid["行业"], x=ind_valid["平均碳排放(吨)"],
                            orientation="h",
                            marker=dict(
                                color=ind_valid["平均碳排放(吨)"],
                                colorscale="reds",
                                showscale=True,
                                colorbar=dict(title="吨", thickness=12, len=0.5),
                            ),
                            text=ind_valid["平均碳排放(吨)"].apply(lambda v: f"{v:,.0f}"),
                            textposition="outside",
                            hovertemplate="%{y}: %{x:,.0f} 吨<extra></extra>",
                        ))
                        fig.update_layout(
                            title=dict(text="各行业平均碳排放", font=dict(size=14)),
                            height=max(350, 25 * len(ind_valid)),
                            margin=dict(l=10, r=10, t=40, b=10),
                            plot_bgcolor="rgba(0,0,0,0)",
                        )
                        st.plotly_chart(polish_fig(fig), use_container_width=True)
                    except Exception:
                        pass

        # 关键洞察
        st.markdown("---")
        render_section("关键数据洞察")
        for ins in insights:
            st.info(f"**[{ins['类别']}]** {ins['洞察']}")

    except Exception as e:
        st.warning(f"分析模块暂不可用: {e}")
        st.info("请运行: python run.py analyze")

# ====== AI智能助手页 ======
elif page == "AI智能助手":
    from src.app.pages.ai_assistant import render_ai_assistant_page
    render_ai_assistant_page()

# ====== 数据管理页 ======
elif page == "数据管理":
    st.title("数据管理")

    tab1, tab2, tab3 = st.tabs(["数据导入", "数据导出", "数据库状态"])

    with tab1:
        render_section("运行数据提取流水线")
        st.markdown("""
        | 步骤 | 命令 | 说明 |
        |------|------|------|
        | 1. 下载 | `python run.py download` | 从巨潮资讯网下载ESG报告PDF |
        | 2. 预处理 | `python run.py preprocess` | PDF文本+表格提取为Markdown |
        | 3. 提取 | `python run.py extract` | DeepSeek大模型提取ESG指标 |
        | 4. 校验 | `python run.py validate` | 校验提取结果质量 |
        | 5. 入库 | `python run.py db-import` | 导入SQLite数据库 |
        | 6. 可视化 | `python run.py app` | 启动本应用 |
        """)

    with tab2:
        render_section("导出数据")
        results = load_all_results()
        if results:
            df = build_dataframe(results)

            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("导出CSV（含BOM，Excel可直接打开）", csv, "esg_extracted_data.csv", "text/csv")

            json_str = json.dumps(results, ensure_ascii=False, indent=2)
            st.download_button("导出完整JSON", json_str, "esg_extracted_data.json", "application/json")

            # 仅定量数据导出
            qt_df = df[df["类型"] == "定量"] if not df.empty else pd.DataFrame()
            if not qt_df.empty:
                qt_csv = qt_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("仅导出定量指标CSV", qt_csv, "esg_quantitative.csv", "text/csv")

    with tab3:
        render_section("数据库状态")
        db = get_db()
        if db:
            try:
                s = db.get_statistics()
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("公司数", s["companies"])
                with col2:
                    st.metric("报告数", s["reports"])
                with col3:
                    st.metric("已提取", s["reports_done"])
                with col4:
                    st.metric("指标值", s["extracted_values"] + s["extracted_texts"])

                # 行业统计
                industry_stats = db.get_industry_stats()
                if industry_stats:
                    st.markdown("---")
                    render_section("行业分布")
                    st.dataframe(pd.DataFrame(industry_stats), use_container_width=True)
            except Exception as e:
                st.error(f"数据库读取失败: {e}")
        else:
            st.warning("数据库未初始化。请运行: python run.py db-import")
            if BASE_DIR.joinpath("data", "output").exists():
                json_count = len(list(BASE_DIR.joinpath("data", "output").glob("*_result.json")))
                st.info(f"检测到 {json_count} 个JSON提取结果，可导入数据库。")


if __name__ == "__main__":
    st.write("请用 `streamlit run src/app/main.py` 启动应用")

