"""ESG分析系统 FastAPI 后端入口"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，以便复用 src/ 下的模块
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import data, companies, indicators, analysis, comparison, ai, trends, benchmark

app = FastAPI(
    title="ESG Analysis API",
    description="ESG数据智能提取与分析系统 — REST API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api")
app.include_router(companies.router, prefix="/api")
app.include_router(indicators.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(trends.router, prefix="/api")
app.include_router(benchmark.router, prefix="/api")


@app.get("/")
def root():
    return {"service": "ESG Analysis API", "docs": "/docs"}
