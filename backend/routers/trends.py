"""趋势分析 API"""
import logging
from collections import defaultdict
from fastapi import APIRouter, Query, HTTPException

from backend.dependencies import get_adapter
from backend.schemas.benchmark import TrendPoint, CompanyTrend

logger = logging.getLogger(__name__)
router = APIRouter(tags=["趋势分析"])


@router.get("/trends/company/{company_name}")
def get_company_trend(company_name: str):
    """获取公司跨年度ESG表现趋势"""
    adapter = get_adapter()

    info = adapter.company_index.get(company_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到公司 '{company_name}'")

    # 收集该公司所有年份的报告
    years_data = []
    for raw in adapter.raw_results:
        if raw.get("company_name") == company_name:
            years_data.append(raw)

    years_data.sort(key=lambda r: r.get("report_year", ""))

    # 构建 E/S/G 得分趋势
    esg_trend: dict[str, list] = {"E": [], "S": [], "G": [], "ESG综合": []}

    for r in years_data:
        yr = str(r.get("report_year", ""))
        # 用analyzer逻辑计算该年份得分
        from src.analyzer import compute_esg_scores, load_clean_data
        df = adapter.df

        # 筛选该公司数据
        company_df = df[(df["公司"] == company_name) & (df["年份"] == yr)]
        if company_df.empty:
            continue

        # 简单E/S/G评分
        e_score = s_score = g_score = 0
        e_count = s_count = g_count = 0

        for _, row in company_df.iterrows():
            ind_id = row["指标ID"]
            val = row["数值"]
            if not ind_id or val is None:
                continue
            if ind_id.startswith("E_"):
                e_score += 1 if ind_id != "E_Q06" else min(val / 100, 1)
                if ind_id == "E_Q06":
                    e_score += min(val / 100, 1) - 1  # 修正
                    e_score += min(val / 100, 1)
                e_count += 1
            elif ind_id.startswith("S_"):
                s_count += 1
                if ind_id == "S_Q05":
                    s_score += min(val / 100, 1)
                elif ind_id == "S_Q08":
                    s_score += min(val / 20, 1)
                elif ind_id == "S_Q02":
                    s_score += min(val / 50, 1)
            elif ind_id.startswith("G_"):
                g_count += 1
                if ind_id == "G_Q02":
                    g_score += min(val / 50, 1)
                elif ind_id == "G_Q04":
                    g_score += min(val / 12, 1)

        # 使用已有的score数据（如果存在）
        score_row = adapter.scores[adapter.scores["公司"] == company_name] if not adapter.scores.empty else None
        if score_row is not None and len(score_row) > 0:
            row_data = score_row.iloc[0]
            esg_trend["E"].append({"year": yr, "value": row_data.get("E_得分", None)})
            esg_trend["S"].append({"year": yr, "value": row_data.get("S_得分", None)})
            esg_trend["G"].append({"year": yr, "value": row_data.get("G_得分", None)})
            esg_trend["ESG综合"].append({"year": yr, "value": row_data.get("ESG综合", None)})

    # 关键指标趋势
    key_ids = ["E_Q01", "E_Q06", "S_Q02", "S_Q05", "S_Q08", "G_Q02", "G_Q04"]
    indicator_trends = {}
    for ind_id in key_ids:
        ind_def = adapter.indicator_map.get(ind_id)
        if not ind_def:
            continue
        points = []
        for r in years_data:
            yr = str(r.get("report_year", ""))
            for item in r.get("quantitative_indicators", []):
                if item.get("id") == ind_id:
                    points.append({"year": yr, "value": item.get("value")})
        if points:
            indicator_trends[ind_def.name] = points

    return CompanyTrend(
        company=company_name,
        industry=info.get("industry", ""),
        esg_trend={k: [TrendPoint(year=p["year"], value=p["value"]) for p in v] for k, v in esg_trend.items()},
        indicator_trends={k: [TrendPoint(year=p["year"], value=p["value"]) for p in v] for k, v in indicator_trends.items()},
    )


@router.get("/trends/industry/{industry}")
def get_industry_trend(industry: str):
    """获取行业ESG指标均值趋势"""
    adapter = get_adapter()
    if industry not in adapter.industries_list:
        raise HTTPException(status_code=404, detail=f"未找到行业 '{industry}'")

    ind_df = adapter.df[adapter.df["行业"] == industry]
    if ind_df.empty:
        return {"industry": industry, "trends": {}}

    years = sorted(ind_df["年份"].unique())
    trends = {}

    key_ids = ["E_Q01", "E_Q06", "S_Q02", "S_Q05", "S_Q08", "G_Q02", "G_Q04"]
    for ind_id in key_ids:
        ind_def = adapter.indicator_map.get(ind_id)
        if not ind_def:
            continue
        points = []
        for yr in years:
            yr_data = ind_df[(ind_df["指标ID"] == ind_id) & (ind_df["年份"] == yr)]["数值"]
            if len(yr_data.dropna()) > 0:
                points.append({"year": str(yr), "value": round(float(yr_data.dropna().mean()), 4)})
        if points:
            trends[ind_def.name] = points

    return {"industry": industry, "company_count": int(ind_df["公司"].nunique()), "trends": trends}


@router.get("/trends/indicator/{indicator_id}")
def get_indicator_trend(indicator_id: str):
    """获取某个指标在各行业/年度的趋势"""
    adapter = get_adapter()
    if indicator_id not in adapter.indicator_map:
        raise HTTPException(status_code=404, detail=f"指标不存在: {indicator_id}")

    ind_def = adapter.indicator_map[indicator_id]
    subset = adapter.df[adapter.df["指标ID"] == indicator_id].dropna(subset=["数值"])
    if subset.empty:
        return {"indicator_id": indicator_id, "indicator_name": ind_def.name, "data": []}

    # 按行业×年份聚合
    summary = (
        subset.groupby(["行业", "年份"])["数值"]
        .mean()
        .round(3)
        .reset_index()
        .rename(columns={"数值": "mean_value"})
    )

    return {
        "indicator_id": indicator_id,
        "indicator_name": ind_def.name,
        "unit": ind_def.unit,
        "by_industry": summary.to_dict(orient="records"),
        "overall_mean": round(float(subset["数值"].mean()), 3),
    }
