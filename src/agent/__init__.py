"""ESG可视化智能体包。"""

__all__ = [
    "ESGDataAdapter",
    "ESGQueryAgent",
    "create_agent",
    "TOOL_SCHEMAS",
    "execute_tool",
]


def __getattr__(name):
    if name == "ESGDataAdapter":
        from src.agent.data_adapter import ESGDataAdapter
        return ESGDataAdapter
    if name in {"ESGQueryAgent", "create_agent"}:
        from src.agent.query_engine import ESGQueryAgent, create_agent
        return {"ESGQueryAgent": ESGQueryAgent, "create_agent": create_agent}[name]
    if name in {"TOOL_SCHEMAS", "execute_tool"}:
        from src.agent.tools import TOOL_SCHEMAS, execute_tool
        return {"TOOL_SCHEMAS": TOOL_SCHEMAS, "execute_tool": execute_tool}[name]
    raise AttributeError(name)
