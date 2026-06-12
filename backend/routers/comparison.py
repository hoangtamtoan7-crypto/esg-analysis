"""指标对比 API"""
import logging
from fastapi import APIRouter, Query

from backend.dependencies import get_adapter
from backend.schemas.benchmark import MatrixRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["指标对比"])


@router.get("/comparison")
def get_comparison_data(
    indicator_id: str = Query(..., description="指标ID，如 E_Q01"),
    dimension: str | None = Query(None, description="筛选维度 E/S/G"),
    top_n: int = Query(20, ge=1, le=100),
):
    """按指标获取各公司对比数据，返回降序排列的TOP N"""
    adapter = get_adapter()

    # 如果有维度筛选，先检查指标是否属于该维度
    if dimension:
        if not indicator_id.startswith(dimension + "_"):
            return {"error": f"指标 {indicator_id} 不属于维度 {dimension}", "data": [], "unit": "", "indicator_name": ""}

    ind_def = adapter.indicator_map.get(indicator_id)
    name = ind_def.name if ind_def else indicator_id
    unit = ind_def.unit if ind_def else ""

    subset = adapter.df[adapter.df["指标ID"] == indicator_id].dropna(subset=["数值"])
    if subset.empty:
        return {"indicator_id": indicator_id, "indicator_name": name, "unit": unit, "data": [], "count": 0}

    # 同一公司取最大数值
    chart_data = (
        subset.sort_values("数值", ascending=False)
        .groupby("公司", as_index=False)
        .first()
        .sort_values("数值", ascending=False)
        .head(top_n)
    )

    data = []
    for _, row in chart_data.iterrows():
        data.append({
            "company": row["公司"],
            "industry": row.get("行业", ""),
            "year": str(row.get("年份", "")),
            "value": None if row["数值"] is None or str(row["数值"]) == "nan" else float(row["数值"]),
            "unit": row.get("单位", ""),
            "confidence": row.get("置信度", ""),
        })

    return {
        "indicator_id": indicator_id,
        "indicator_name": name,
        "unit": unit,
        "description": ind_def.description if ind_def else "",
        "data": data,
        "count": len(data),
    }


@router.get("/comparison/multi")
def compare_multi_companies(
    companies: str = Query(..., description="逗号分隔的公司名称"),
    indicators: str | None = Query(None, description="逗号分隔的指标ID，默认使用关键指标"),
):
    """多公司多指标对比"""
    adapter = get_adapter()
    company_list = [c.strip() for c in companies.split(",") if c.strip()]

    if indicators:
        indicator_ids = [i.strip() for i in indicators.split(",") if i.strip()]
        # 解析指标
        resolved = []
        for iid in indicator_ids:
            if iid in adapter.indicator_map:
                ind_def = adapter.indicator_map[iid]
                resolved.append({"id": iid, "name": ind_def.name, "unit": ind_def.unit})
    else:
        default_ids = ["E_Q01", "E_Q06", "S_Q02", "S_Q08", "G_Q02", "G_Q04"]
        resolved = [
            {"id": iid, "name": adapter.indicator_map[iid].name, "unit": adapter.indicator_map[iid].unit}
            for iid in default_ids if iid in adapter.indicator_map
        ]

    comparisons = []
    for company in company_list:
        info = adapter.company_index.get(company)
        if not info:
            comparisons.append({"company": company, "industry": "", "year": "", "error": "未找到"})
            continue

        row_data = {"company": company, "industry": info.get("industry", ""), "year": info.get("year", "")}
        qt_by_id = {item.get("id"): item for item in info.get("quantitative", [])}
        for r in resolved:
            item = qt_by_id.get(r["id"])
            row_data[r["name"]] = item.get("value") if item else None
        comparisons.append(row_data)

    return {
        "indicators": resolved,
        "data": comparisons,
    }


@router.post("/comparison/matrix")
def comparison_matrix(req: MatrixRequest):
    """多公司 × 多指标矩阵对比 — 返回二维矩阵 + 行业均值行"""
    adapter = get_adapter()

    # 解析指标
    resolved = []
    for iid in req.indicator_ids:
        ind_def = adapter.indicator_map.get(iid)
        if ind_def:
            resolved.append({"id": iid, "name": ind_def.name, "unit": ind_def.unit})

    if not resolved:
        return {"error": "未找到有效指标", "matrix": [], "indicators": [], "industry_averages": []}

    # 构建矩阵
    matrix = []
    industries_seen = set()
    for company in req.companies:
        info = adapter.company_index.get(company)
        if not info:
            matrix.append({"company": company, "industry": "", "year": "", "error": "未找到", "values": {}})
            continue

        industries_seen.add(info.get("industry", ""))
        qt_by_id = {item.get("id"): item for item in info.get("quantitative", [])}
        values = {}
        for r in resolved:
            item = qt_by_id.get(r["id"])
            values[r["id"]] = item.get("value") if item else None

        matrix.append({
            "company": company,
            "industry": info.get("industry", ""),
            "year": info.get("year", ""),
            "values": values,
        })

    # 行业均值行
    industry_averages = []
    for industry in industries_seen:
        ind_data = adapter.df[adapter.df["行业"] == industry]
        avg_values = {}
        for r in resolved:
            vals = ind_data[ind_data["指标ID"] == r["id"]]["数值"].dropna()
            avg_values[r["id"]] = round(float(vals.mean()), 3) if len(vals) > 0 else None
        industry_averages.append({
            "label": f"{industry} (行业均值)",
            "industry": industry,
            "values": avg_values,
        })

    return {
        "indicators": resolved,
        "matrix": matrix,
        "industry_averages": industry_averages,
    }
