from pydantic import BaseModel
from typing import Optional


class IndicatorDef(BaseModel):
    id: str
    name: str
    name_en: Optional[str] = None
    dimension: str  # E/S/G
    indicator_type: str  # quantitative/qualitative
    unit: Optional[str] = None
    keywords: list[str] = []
    description: Optional[str] = None


class IndicatorValueRow(BaseModel):
    company: str
    stock_code: str
    industry: str
    year: str
    value: Optional[float] = None
    unit: Optional[str] = None
    confidence: Optional[str] = None
