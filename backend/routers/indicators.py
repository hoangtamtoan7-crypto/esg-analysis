"""指标体系 API"""
import logging
from fastapi import APIRouter, Query, HTTPException

from backend.dependencies import get_adapter
from backend.schemas.indicator import IndicatorDef, IndicatorValueRow
from src.extractor.indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION

logger = logging.getLogger(__name__)
router = APIRouter(tags=["指标体系"])


@router.get("/indicators", response_model=list[IndicatorDef])
def list_indicators(
    dimension: str | None = Query(None, description="筛选维度 E/S/G"),
    keyword: str | None = Query(None, description="关键词搜索"),
    indicator_type: str | None = Query(None, description="类型 quantitative/qualitative"),
):
    adapter = get_adapter()
    results = adapter.get_indicators(dimension=dimension, keyword=keyword)
    output = []
    for item in results:
        if indicator_type and item.get("type") != indicator_type:
            continue
        ind_id = item["id"]
        # 从原始指标定义中获取完整信息
        original = adapter.indicator_map.get(ind_id)
        output.append(IndicatorDef(
            id=ind_id,
            name=item["name"],
            name_en=original.name_en if original else None,
            dimension=item["dimension"],
            indicator_type=item["type"],
            unit=item.get("unit"),
            keywords=original.keywords if original else [],
            description=item.get("description"),
        ))
    return output


@router.get("/indicators/{indicator_id}")
def get_indicator_detail(indicator_id: str):
    adapter = get_adapter()
    original = adapter.indicator_map.get(indicator_id)
    if not original:
        raise HTTPException(status_code=404, detail=f"未找到指标 '{indicator_id}'")

    # 获取该指标有数据的公司
    subset = adapter.df[adapter.df["指标ID"] == indicator_id].dropna(subset=["数值"])
    if subset.empty:
        return {
            "indicator": IndicatorDef(
                id=original.id,
                name=original.name,
                name_en=original.name_en,
                dimension=original.dimension,
                indicator_type=original.indicator_type,
                unit=original.unit,
                keywords=original.keywords,
                description=original.description,
            ),
            "values": [],
            "company_count": 0,
        }

    top = subset.nlargest(min(30, len(subset)), "数值")
    values = []
    for _, row in top.iterrows():
        values.append(IndicatorValueRow(
            company=row["公司"],
            stock_code="",
            industry=row.get("行业", ""),
            year=str(row.get("年份", "")),
            value=row["数值"],
            unit=row.get("单位", ""),
            confidence=row.get("置信度", ""),
        ))

    return {
        "indicator": IndicatorDef(
            id=original.id,
            name=original.name,
            name_en=original.name_en,
            dimension=original.dimension,
            indicator_type=original.indicator_type,
            unit=original.unit,
            keywords=original.keywords,
            description=original.description,
        ),
        "values": values,
        "company_count": len(values),
    }


@router.get("/indicators/filters/metadata")
def get_filters_metadata():
    """返回筛选面板所需的元数据（行业列表、年份范围、质量等级分布）"""
    adapter = get_adapter()
    return {
        "industries": sorted(adapter.industries_list),
        "years": sorted(set(str(r.get("report_year", "")) for r in adapter.raw_results if r.get("report_year"))),
        "dimensions": ["E", "S", "G"],
        "indicator_types": ["quantitative", "qualitative"],
        "quality_range": {"min": 0.0, "max": 1.0},
        "total_companies": len(adapter.companies),
        "total_indicators": len(adapter.indicator_map),
    }
