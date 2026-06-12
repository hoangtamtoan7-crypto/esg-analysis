"""公司详情 API"""
import logging
from fastapi import APIRouter, Query, HTTPException

from backend.dependencies import get_adapter
from backend.schemas.company import CompanyBase, CompanyDetail, IndicatorValue, QualitativeValue, ESGScores

logger = logging.getLogger(__name__)
router = APIRouter(tags=["公司详情"])


@router.get("/companies", response_model=list[CompanyBase])
def list_companies(industry: str | None = Query(None, description="按行业筛选")):
    adapter = get_adapter()
    results = adapter.get_companies(industry=industry)
    return [
        CompanyBase(
            stock_code="",
            name=r["公司"],
            industry=r.get("行业", ""),
        )
        for r in results
    ]


@router.get("/companies/search")
def search_companies(q: str = Query(..., description="搜索关键词")):
    adapter = get_adapter()
    matches = adapter._fuzzy_match_company(q)
    # 整理信息
    results = []
    for name in matches:
        info = adapter.company_index.get(name, {})
        score_row = adapter.scores[adapter.scores["公司"] == name] if not adapter.scores.empty else None
        item = {
            "name": name,
            "industry": info.get("industry", ""),
            "year": info.get("year", ""),
            "quality": info.get("quality", 0),
            "coverage": info.get("coverage", 0),
        }
        if score_row is not None and len(score_row) > 0:
            item["esg_scores"] = {
                "rank": int(score_row["排名"].iloc[0]) if "排名" in score_row.columns else None,
                "e_score": score_row["E_得分"].iloc[0],
                "s_score": score_row["S_得分"].iloc[0],
                "g_score": score_row["G_得分"].iloc[0],
                "esg_composite": score_row["ESG综合"].iloc[0],
            }
        results.append(item)
    return results


@router.get("/companies/{company_name}")
def get_company_detail(company_name: str, dimension: str | None = Query(None, description="筛选维度 E/S/G")):
    """获取公司ESG详情 — 包含E/S/G维度指标及得分"""
    adapter = get_adapter()
    data = adapter.get_company_data(company_name, dimension=dimension)

    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])

    score_data = data.get("ESG得分", {})
    esg_scores = ESGScores(
        rank=score_data.get("排名"),
        e_score=score_data.get("E_得分", 0),
        s_score=score_data.get("S_得分", 0),
        g_score=score_data.get("G_得分", 0),
        esg_composite=score_data.get("ESG综合", 0),
    ) if score_data else None

    quantitative = [
        IndicatorValue(
            indicator_id=item.get("指标ID", ""),
            indicator_name=item.get("指标名称", ""),
            value=item.get("数值"),
            unit=item.get("单位", ""),
            confidence=item.get("置信度", ""),
            original_text=item.get("原文"),
        )
        for item in data.get("定量指标", [])
    ]

    qualitative = [
        QualitativeValue(
            indicator_id=item.get("指标ID", ""),
            indicator_name=item.get("指标名称", ""),
            status=item.get("状态", ""),
            summary=item.get("摘要", ""),
            confidence=item.get("置信度", ""),
        )
        for item in data.get("定性指标", [])
    ]

    return CompanyDetail(
        stock_code="",
        name=company_name,
        industry=data.get("行业", ""),
        report_year=data.get("年份", ""),
        quality_score=data.get("质量分", 0),
        coverage=data.get("覆盖度", 0),
        esg_scores=esg_scores,
        quantitative_indicators=quantitative,
        qualitative_indicators=qualitative,
    )
