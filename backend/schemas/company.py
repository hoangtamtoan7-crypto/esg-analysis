from pydantic import BaseModel
from typing import Optional


class CompanyBase(BaseModel):
    stock_code: str
    name: str
    exchange: Optional[str] = None
    market: Optional[str] = None
    industry: Optional[str] = None


class IndicatorValue(BaseModel):
    indicator_id: str
    indicator_name: str
    value: Optional[float] = None
    unit: str
    confidence: str
    original_text: Optional[str] = None


class QualitativeValue(BaseModel):
    indicator_id: str
    indicator_name: str
    status: str  # yes/no/partial
    summary: str
    confidence: str
    original_text: Optional[str] = None


class ESGScores(BaseModel):
    rank: Optional[int] = None
    e_score: float
    s_score: float
    g_score: float
    esg_composite: float


class CompanyDetail(CompanyBase):
    report_year: str
    quality_score: float
    coverage: float
    esg_scores: Optional[ESGScores] = None
    quantitative_indicators: list[IndicatorValue] = []
    qualitative_indicators: list[QualitativeValue] = []
