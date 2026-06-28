"""Streamlit trend analysis page."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = BASE_DIR / "data" / "output"
HUAZHENG_PATH = BASE_DIR / "data" / "analysis" / "huazheng_esg_quarterly.json"

KEY_INDICATORS = {
    "E_Q01",
    "E_Q04",
    "E_Q06",
    "E_Q07",
    "S_Q01",
    "S_Q02",
    "S_Q05",
    "S_Q06",
    "S_Q08",
    "G_Q02",
    "G_Q04",
}

DIMENSION_COLORS = {
    "综合得分": "#4f46e5",
    "E得分": "#2e7d32",
    "S得分": "#1565c0",
    "G得分": "#e65100",
}


def _parse_file_meta(path: Path) -> tuple[str, str]:
    match = re.match(r"^(\d{6})_.+?_(\d{4})_result\.json$", path.name)
    if match:
        return match.group(1), match.group(2)

    code_match = re.match(r"^(\d{6})_", path.name)
    year_match = re.search(r"_(19\d{2}|20\d{2})_", path.name)
    return code_match.group(1) if code_match else "", year_match.group(1) if year_match else ""


@st.cache_data(show_spinner=False)
def load_huazheng_quarterly() -> pd.DataFrame:
    if not HUAZHENG_PATH.exists():
        return pd.DataFrame()

    rows = json.loads(HUAZHENG_PATH.read_text(encoding="utf-8"))
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for col in ["composite_score", "e_score", "s_score", "g_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["year"] = df["year"].astype(str)
    return df


@st.cache_data(show_spinner=False)
def load_json_indicator_points() -> dict[str, list[dict]]:
    reports_by_code: dict[str, list[dict]] = {}
    if not OUTPUT_DIR.exists():
        return reports_by_code

    for path in sorted(OUTPUT_DIR.glob("*_result.json")):
        code, file_year = _parse_file_meta(path)
        if not code:
            continue

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        year = str(raw.get("report_year") or file_year or "")
        if not year:
            continue

        points = []
        for item in raw.get("quantitative_indicators", []):
            ind_id = item.get("id") or item.get("indicator_id")
            value = item.get("value")
            if ind_id not in KEY_INDICATORS or value is None:
                continue
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                continue
            points.append(
                {
                    "year": year,
                    "indicator_id": ind_id,
                    "indicator": item.get("name") or item.get("indicator_name") or ind_id,
                    "value": numeric_value,
                    "unit": item.get("unit") or "",
                    "confidence": item.get("confidence") or "",
                }
            )

        reports_by_code.setdefault(code, []).append(
            {
                "year": year,
                "company": raw.get("company_name", ""),
                "points": points,
            }
        )

    return reports_by_code


def _annual_rating(df: pd.DataFrame, code: str) -> pd.DataFrame:
    company_df = df[df["stock_code"] == code].copy()
    if company_df.empty:
        return company_df

    annual = (
        company_df.groupby("year", as_index=False)
        .agg(
            公司=("company", "last"),
            行业=("industry_cs", "last"),
            综合评级=("rating", "last"),
            E评级=("e_rating", "last"),
            S评级=("s_rating", "last"),
            G评级=("g_rating", "last"),
            综合得分=("composite_score", "mean"),
            E得分=("e_score", "mean"),
            S得分=("s_score", "mean"),
            G得分=("g_score", "mean"),
            季度数=("quarter", "count"),
        )
        .sort_values("year")
    )
    for col in ["综合得分", "E得分", "S得分", "G得分"]:
        annual[col] = annual[col].round(2)
    return annual


def _build_rating_chart(annual: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in ["综合得分", "E得分", "S得分", "G得分"]:
        fig.add_trace(
            go.Scatter(
                x=annual["year"],
                y=annual[col],
                mode="lines+markers",
                name=col,
                line=dict(color=DIMENSION_COLORS[col], width=3 if col == "综合得分" else 2),
                marker=dict(size=8 if col == "综合得分" else 6),
                hovertemplate=f"%{{x}}<br>{col}: %{{y:.2f}}<extra></extra>",
            )
        )

    fig.update_layout(
        height=430,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(title="年度季度均分", range=[0, 100]),
        xaxis=dict(title="年份"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _indicator_trends(reports: list[dict]) -> dict[str, pd.DataFrame]:
    buckets: dict[str, list[dict]] = {}
    for report in reports:
        for point in report.get("points", []):
            buckets.setdefault(point["indicator"], []).append(point)

    trends = {}
    for indicator, points in buckets.items():
        df = pd.DataFrame(points)
        if df.empty:
            continue
        df = (
            df.sort_values("year")
            .drop_duplicates(subset=["year"], keep="last")
            .sort_values("year")
        )
        trends[indicator] = df
    return trends


def _build_indicator_chart(name: str, data: pd.DataFrame) -> go.Figure:
    unit = data["unit"].dropna().iloc[0] if "unit" in data and data["unit"].notna().any() else ""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["year"],
            y=data["value"],
            mode="lines+markers",
            name=name,
            fill="tozeroy",
            line=dict(color="#2e7d32", width=2),
            marker=dict(size=7),
            hovertemplate=f"%{{x}}<br>{name}: %{{y:,.2f}} {unit}<extra></extra>",
        )
    )
    fig.update_layout(
        height=270,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(title=unit),
        xaxis=dict(title="年份"),
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def _render_insights(company: str, annual: pd.DataFrame, trends: dict[str, pd.DataFrame]) -> None:
    insights = []
    if len(annual) >= 2:
        first = annual.iloc[0]
        last = annual.iloc[-1]
        delta = float(last["综合得分"] - first["综合得分"])
        insights.append(
            (
                "评级变化",
                f"{company} 华证ESG综合得分从 {first['year']} 年 {first['综合得分']:.2f} 变为 "
                f"{last['year']} 年 {last['综合得分']:.2f}，累计变化 {delta:+.2f} 分。",
            )
        )

        dim_deltas = []
        for col in ["E得分", "S得分", "G得分"]:
            dim_deltas.append((col, float(last[col] - first[col])))
        dim, dim_delta = max(dim_deltas, key=lambda item: abs(item[1]))
        insights.append(("维度波动", f"{dim} 是区间内变化最大的维度，累计变化 {dim_delta:+.2f} 分。"))

    best_indicator = sorted(trends.items(), key=lambda item: len(item[1]), reverse=True)
    if best_indicator:
        name, data = best_indicator[0]
        if len(data) >= 2:
            first = data.iloc[0]
            last = data.iloc[-1]
            delta = float(last["value"] - first["value"])
            insights.append(
                (
                    "抽取指标",
                    f"{name} 已形成 {len(data)} 个年度观测点，从 {first['year']} 年到 "
                    f"{last['year']} 年变化 {delta:+,.2f}。",
                )
            )

    if not insights:
        return

    cols = st.columns(len(insights))
    for col, (title, text) in zip(cols, insights):
        with col:
            st.info(f"**{title}**\n\n{text}")


def render_trends_page() -> None:
    st.title("趋势分析")
    st.caption("结合华证ESG季度评级表与大模型抽取JSON，展示公司评级趋势、关键指标趋势和行业均值趋势。")

    rating_df = load_huazheng_quarterly()
    reports_by_code = load_json_indicator_points()
    if rating_df.empty:
        st.warning("未找到华证ESG趋势数据，请先生成 data/analysis/huazheng_esg_quarterly.json。")
        return

    company_meta = (
        rating_df.sort_values(["stock_code", "year"])
        .groupby("stock_code", as_index=False)
        .agg(公司=("company", "last"), 行业=("industry_cs", "last"))
        .sort_values("stock_code")
    )

    st.metric("华证评级观测", f"{len(rating_df):,} 条")
    st.metric("覆盖公司", f"{company_meta['stock_code'].nunique():,} 家")

    options = {
        f"{row.stock_code} · {row.公司}": row.stock_code
        for row in company_meta.itertuples(index=False)
    }
    selected_label = st.selectbox("选择公司", list(options.keys()))
    selected_code = options[selected_label]

    annual = _annual_rating(rating_df, selected_code)
    if annual.empty:
        st.info("该公司暂无年度趋势数据。")
        return

    company = annual["公司"].iloc[-1]
    industry = annual["行业"].iloc[-1]
    st.subheader(f"{company} ESG评级年度趋势")
    st.caption(f"{selected_code} · {industry} · 年度值按季度评级均分计算")

    first = annual.iloc[0]
    last = annual.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    for col, metric_name in zip([col1, col2, col3, col4], ["综合得分", "E得分", "S得分", "G得分"]):
        delta = float(last[metric_name] - first[metric_name])
        col.metric(metric_name, f"{last[metric_name]:.2f}", f"{delta:+.2f}")

    st.plotly_chart(_build_rating_chart(annual), use_container_width=True)

    reports = reports_by_code.get(selected_code, [])
    indicator_trends = _indicator_trends(reports)
    _render_insights(company, annual, indicator_trends)

    st.markdown("---")
    st.subheader("JSON抽取指标年度趋势")
    if indicator_trends:
        items = sorted(indicator_trends.items(), key=lambda item: len(item[1]), reverse=True)[:6]
        for i in range(0, len(items), 2):
            cols = st.columns(2)
            for col, (name, data) in zip(cols, items[i : i + 2]):
                with col:
                    st.markdown(f"**{name}**")
                    st.plotly_chart(_build_indicator_chart(name, data), use_container_width=True)
    else:
        st.info("该公司在当前仓库 JSON 结果中暂无可展示的关键定量指标年度序列。")

    st.markdown("---")
    st.subheader("行业ESG综合均值趋势")
    industries = sorted(rating_df["industry_cs"].dropna().unique().tolist())
    default_index = industries.index(industry) if industry in industries else 0
    selected_industry = st.selectbox("选择行业", industries, index=default_index)

    industry_df = rating_df[rating_df["industry_cs"] == selected_industry]
    industry_annual = (
        industry_df.groupby("year", as_index=False)
        .agg(综合均分=("composite_score", "mean"), 公司数=("stock_code", "nunique"))
        .sort_values("year")
    )
    industry_annual["综合均分"] = industry_annual["综合均分"].round(2)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=industry_annual["year"],
            y=industry_annual["综合均分"],
            mode="lines+markers",
            name=selected_industry,
            line=dict(color="#1677FF", width=3),
            marker=dict(size=7),
            customdata=industry_annual["公司数"],
            hovertemplate="%{x}<br>综合均分: %{y:.2f}<br>公司数: %{customdata}<extra></extra>",
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(title="行业综合均分", range=[0, 100]),
        xaxis=dict(title="年份"),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("查看年度评级明细"):
        st.dataframe(annual, use_container_width=True, hide_index=True)
