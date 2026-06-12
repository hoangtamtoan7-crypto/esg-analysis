from pydantic import BaseModel
from typing import Optional


class IndustryBenchmark(BaseModel):
    industry: str
    company_count: int
    indicator_id: str
    indicator_name: str
    unit: str
    mean: float
    median: float
    p25: float
    p75: float
    min_val: Optional[float] = None
    max_val: Optional[float] = None


class ScreenRequest(BaseModel):
    conditions: list[dict] = []
    """每个条件: {indicator_id, op ('gt'/'lt'/'gte'/'lte'), value}"""
    esg_e_min: Optional[float] = None
    esg_s_min: Optional[float] = None
    esg_g_min: Optional[float] = None
    esg_composite_min: Optional[float] = None
    industry: Optional[str] = None
    quality_min: Optional[float] = None
    limit: int = 50


class ComplianceItem(BaseModel):
    indicator_id: str
    indicator_name: str
    dimension: str
    indicator_type: str
    disclosure_rate: float
    industry_breakdown: list[dict] = []


class TrendPoint(BaseModel):
    year: str
    value: Optional[float] = None


class CompanyTrend(BaseModel):
    company: str
    industry: str
    esg_trend: dict[str, list[TrendPoint]] = {}
    indicator_trends: dict[str, list[TrendPoint]] = {}



class MatrixRequest(BaseModel):
    companies: list[str]
    indicator_ids: list[str]
    year: Optional[str] = None
