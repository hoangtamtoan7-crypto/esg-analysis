from pydantic import BaseModel
from typing import Optional


class ESGScoreRow(BaseModel):
    排名: int
    公司: str
    行业: str
    E_得分: float
    S_得分: float
    G_得分: float
    ESG综合: float


class IndustryRow(BaseModel):
    行业: str
    公司数: int
    平均碳排放_吨: Optional[float] = None
    平均可再生比例_pct: Optional[float] = None
    平均女性员工_pct: Optional[float] = None
    平均研发占比_pct: Optional[float] = None


class Insight(BaseModel):
    类别: str
    洞察: str


class DistributionBin(BaseModel):
    center: float
    count: int


class DimensionDistribution(BaseModel):
    dimension: str
    name: str
    mean: float
    bins: list[DistributionBin]
