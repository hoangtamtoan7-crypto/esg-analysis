from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []


class TableData(BaseModel):
    title: Optional[str] = None
    headers: list[str]
    rows: list[list]


class ChatResponse(BaseModel):
    text: str
    tables: list[TableData] = []
