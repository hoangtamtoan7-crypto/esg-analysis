"""行业对标与投资分析 API"""
import logging
import numpy as np
from fastapi import APIRouter, Query, HTTPException

from backend.dependencies import get_adapter
from backend.schemas.benchmark import (
    IndustryBenchmark, ScreenRequest, ComplianceItem,
    MatrixRequest,
)
from src.extractor.indicators import ALL_INDICATORS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["行业对标与投资"])


@router.get("/benchmark/industry/{industry}")
def get_industry_benchmark(industry: str):
    """获取某个行业的基准数据（均值/中位数/P25/P75）"""
    adapter = get_adapter()

    ind_df = adapter.df[adapter.df["行业"] == industry]
    if ind_df.empty:
        raise HTTPException(status_code=404, detail=f"未找到行业 '{industry}'")

    results = []
    for ind_id, group in ind_df.groupby("指标ID"):
        if group["数值"].dropna().empty:
            continue
        ind_def = adapter.indicator_map.get(ind_id)
        if not ind_def or ind_def.indicator_type != "quantitative":
            continue

        vals = group["数值"].dropna()
        results.append(IndustryBenchmark(
            industry=industry,
            company_count=int(group["公司"].nunique()),
            indicator_id=ind_id,
            indicator_name=ind_def.name,
            unit=ind_def.unit or "",
            mean=round(float(vals.mean()), 3),
            median=round(float(vals.median()), 3),
            p25=round(float(vals.quantile(0.25)), 3),
            p75=round(float(vals.quantile(0.75)), 3),
            min_val=round(float(vals.min()), 3),
            max_val=round(float(vals.max()), 3),
        ))

    return results


@router.get("/benchmark/company/{company_name}")
def get_company_vs_industry(company_name: str):
    """对比公司与所在行业的基准"""
    adapter = get_adapter()
    info = adapter.company_index.get(company_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到公司 '{company_name}'")

    industry = info.get("industry", "")
    benchmarks = get_industry_benchmark(industry)
    benchmark_by_id = {b.indicator_id: b.model_dump() for b in benchmarks}

    comparisons = []
    for item in info.get("quantitative", []):
        ind_id = item.get("id", "")
        val = item.get("value")
        if val is None:
            continue

        bm = benchmark_by_id.get(ind_id, {})
        rank_info = None
        if bm:
            try:
                # 计算该指标在行业中的排名
                ind_data = adapter.df[
                    (adapter.df["指标ID"] == ind_id) &
                    (adapter.df["行业"] == industry)
                ]["数值"].dropna()
                above = (ind_data > val).sum()
                rank_info = {
                    "total": int(len(ind_data)),
                    "rank": int(above + 1),
                    "percentile": round(float(above / len(ind_data) * 100), 1) if len(ind_data) > 0 else None,
                }
            except Exception:
                pass

        benchmark_val = bm.get("median")
        comparisons.append({
            "indicator_id": ind_id,
            "indicator_name": item.get("name", ""),
            "company_value": val,
            "unit": item.get("unit", ""),
            "benchmark_median": benchmark_val,
            "benchmark_mean": bm.get("mean"),
            "benchmark_p25": bm.get("p25"),
            "benchmark_p75": bm.get("p75"),
            "industry_rank": rank_info,
        })

    return {
        "company": company_name,
        "industry": industry,
        "comparisons": comparisons,
    }


@router.post("/investment/screen")
def investment_screen(req: ScreenRequest):
    """投资筛选：按ESG得分和指标阈值筛选公司"""
    adapter = get_adapter()
    if adapter.scores.empty:
        return {"count": 0, "companies": []}

    scores = adapter.scores.copy()

    if req.esg_composite_min is not None:
        scores = scores[scores["ESG综合"] >= req.esg_composite_min]
    if req.esg_e_min is not None:
        scores = scores[scores["E_得分"] >= req.esg_e_min]
    if req.esg_s_min is not None:
        scores = scores[scores["S_得分"] >= req.esg_s_min]
    if req.esg_g_min is not None:
        scores = scores[scores["G_得分"] >= req.esg_g_min]
    if req.industry:
        scores = scores[scores["行业"] == req.industry]

    # 指标阈值筛选
    if req.conditions:
        for cond in req.conditions:
            ind_id = cond.get("indicator_id", "")
            op = cond.get("op", "gt")
            threshold = cond.get("value")

            ind_subset = adapter.df[adapter.df["指标ID"] == ind_id].dropna(subset=["数值"])
            if ind_subset.empty:
                continue

            if op in ("gt", "gte"):
                passing = set(ind_subset[ind_subset["数值"] >= threshold]["公司"].unique())
            else:
                passing = set(ind_subset[ind_subset["数值"] <= threshold]["公司"].unique())

            scores = scores[scores["公司"].isin(passing)]

    result = scores.head(req.limit).to_dict(orient="records")
    return {"count": len(result), "total_matched": len(scores), "companies": result}


@router.get("/policy/compliance", response_model=list[ComplianceItem])
def get_compliance_analysis():
    """信息披露合规分析 — 各指标披露率与行业分布"""
    adapter = get_adapter()
    total_companies = len(adapter.companies)

    results = []
    for ind in ALL_INDICATORS:
        subset = adapter.df[adapter.df["指标ID"] == ind.id]
        companies_with_data = subset["公司"].nunique()
        rate = round(companies_with_data / max(total_companies, 1), 3)

        # 按行业分解
        industry_breakdown = []
        for ind_name, group in subset.groupby("行业"):
            industry_breakdown.append({
                "industry": ind_name,
                "companies_with_data": int(group["公司"].nunique()),
                "disclosure_rate": round(group["公司"].nunique() / max(len(
                    [c for c in adapter.companies if adapter.company_index.get(c, {}).get("industry") == ind_name]
                ), 1), 2),
            })

        results.append(ComplianceItem(
            indicator_id=ind.id,
            indicator_name=ind.name,
            dimension=ind.dimension,
            indicator_type=ind.indicator_type,
            disclosure_rate=rate,
            industry_breakdown=sorted(industry_breakdown, key=lambda x: -x["disclosure_rate"]),
        ))

    return results
