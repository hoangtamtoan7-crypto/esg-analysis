"""数据概览 API"""
import logging
from fastapi import APIRouter

from backend.dependencies import get_adapter, get_db
from src.extractor.indicators import ALL_INDICATORS

logger = logging.getLogger(__name__)
router = APIRouter(tags=["数据概览"])


@router.get("/overview")
def get_overview():
    """获取数据概览 — 公司数、报告数、行业分布等"""
    adapter = get_adapter()
    base = adapter.get_data_overview()

    industry_distribution = []
    for ind_name, count in (
        adapter.df.groupby("行业")["公司"].nunique().sort_values(ascending=False).items()
    ):
        industry_distribution.append({"industry": ind_name, "count": int(count)})

    return {
        "companies": base.get("公司数", 0),
        "reports": base.get("报告数", 0),
        "industries": base.get("行业数", 0),
        "avg_quality_score": base.get("平均质量分", 0),
        "quantitative_indicators": base.get("定量指标数", len([i for i in ALL_INDICATORS if i.indicator_type == "quantitative"])),
        "qualitative_indicators": base.get("定性指标数", len([i for i in ALL_INDICATORS if i.indicator_type == "qualitative"])),
        "industry_distribution": industry_distribution,
    }


@router.get("/stats")
def get_stats():
    """获取数据库统计 + 概要信息"""
    db = get_db()
    if db:
        try:
            s = db.get_statistics()
            return {
                "companies": s["companies"],
                "reports": s["reports"],
                "reports_done": s["reports_done"],
                "extracted_values": s["extracted_values"],
                "extracted_texts": s["extracted_texts"],
            }
        except Exception:
            pass
    return {"companies": 0, "reports": 0, "reports_done": 0, "extracted_values": 0, "extracted_texts": 0}
