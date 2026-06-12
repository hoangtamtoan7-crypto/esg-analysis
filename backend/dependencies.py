"""共享依赖 — 缓存ESGDataAdapter和Database连接"""
from functools import lru_cache

from src.agent.data_adapter import ESGDataAdapter
from src.utils.db import Database


@lru_cache(maxsize=1)
def get_adapter() -> ESGDataAdapter:
    return ESGDataAdapter()


def get_db():
    from pathlib import Path
    db_path = Path(__file__).parent.parent / "data" / "esg_data.db"
    if db_path.exists():
        return Database(str(db_path))
    return None
