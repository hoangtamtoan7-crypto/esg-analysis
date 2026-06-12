"""AI智能助手 API"""
import logging
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.dependencies import get_adapter
from backend.schemas.ai import ChatRequest, ChatResponse, TableData

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI助手"])


# 延迟导入AI模块，避免缺少依赖时导致整个应用无法启动
_agent = None


def _get_agent():
    global _agent
    if _agent is not None:
        return _agent

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return None

    try:
        from src.agent.query_engine import ESGQueryAgent
        adapter = get_adapter()
        _agent = ESGQueryAgent(adapter)
        return _agent
    except Exception as e:
        logger.warning(f"AI Agent初始化失败: {e}")
        return None


@router.post("/ai/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    agent = _get_agent()
    if agent is None:
        raise HTTPException(
            status_code=503,
            detail="AI助手未就绪。请设置 DEEPSEEK_API_KEY 环境变量。",
        )

    try:
        result = agent.query(req.message, chat_history=req.history)

        tables = []
        for tb in result.get("tables", []):
            if isinstance(tb, dict):
                tables.append(TableData(
                    title=tb.get("title"),
                    headers=tb.get("headers", []),
                    rows=tb.get("rows", []),
                ))

        return ChatResponse(
            text=result.get("text", ""),
            tables=tables,
        )
    except Exception as e:
        logger.error(f"AI查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"AI查询失败: {str(e)}")


@router.get("/ai/health")
def ai_health():
    """检查AI助手是否可用"""
    agent = _get_agent()
    if agent is None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return {
            "available": False,
            "reason": "AI助手未就绪，请设置 DEEPSEEK_API_KEY" if not api_key else "Agent初始化失败",
        }
    return {"available": True}
