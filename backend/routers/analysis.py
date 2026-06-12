"""ESG分析 API"""
import logging
import numpy as np
from fastapi import APIRouter, Query

from backend.dependencies import get_adapter
from backend.schemas.analysis import ESGScoreRow, IndustryRow, Insight, DimensionDistribution, DistributionBin
from src.extractor.indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ESG分析"])


@router.get("/analysis/esg-scores", response_model=list[ESGScoreRow])
def get_esg_scores(top_n: int = Query(20, ge=1, le=100)):
    adapter = get_adapter()
    scores = adapter.get_esg_scores(top_n=top_n)
    return [
        ESGScoreRow(
            排名=row.get("排名", i + 1),
            公司=row.get("公司", ""),
            行业=row.get("行业", ""),
            E_得分=row.get("E_得分", 0),
            S_得分=row.get("S_得分", 0),
            G_得分=row.get("G_得分", 0),
            ESG综合=row.get("ESG综合", 0),
        )
        for i, row in enumerate(scores)
    ]


@router.get("/analysis/industries", response_model=list[IndustryRow])
def get_industry_analysis(industry: str | None = Query(None)):
    adapter = get_adapter()
    data = adapter.get_industry_analysis(industry=industry)
    return [
        IndustryRow(
            行业=row.get("行业", ""),
            公司数=row.get("公司数", 0),
            平均碳排放_吨=row.get("平均碳排放(吨)"),
            平均可再生比例_pct=row.get("平均可再生比例(%)"),
            平均女性员工_pct=row.get("平均女性员工(%)"),
            平均研发占比_pct=row.get("平均研发占比(%)"),
        )
        for row in data
    ]


@router.get("/analysis/insights", response_model=list[Insight])
def get_insights():
    adapter = get_adapter()
    return [Insight(类别=ins["类别"], 洞察=ins["洞察"]) for ins in adapter.insights]


@router.get("/analysis/distributions", response_model=list[DimensionDistribution])
def get_distributions():
    adapter = get_adapter()
    if adapter.scores.empty:
        return []

    result = []
    dim_configs = [
        ("E_得分", "E", "环境 (Environmental)"),
        ("S_得分", "S", "社会 (Social)"),
        ("G_得分", "G", "治理 (Governance)"),
    ]

    for col, dim, name in dim_configs:
        data = adapter.scores[col].dropna()
        if len(data) == 0:
            continue

        counts, bin_edges = np.histogram(data.values, bins=25, range=(0, 1))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bins = [DistributionBin(center=round(float(c), 3), count=int(n)) for c, n in zip(bin_centers, counts)]

        result.append(DimensionDistribution(
            dimension=dim,
            name=name,
            mean=round(float(data.mean()), 4),
            bins=bins,
        ))

    return result
