"""DeepSeek API 配置与成本追踪"""

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 尝试从Streamlit Secrets读取（用于Streamlit Cloud部署）
if not DEEPSEEK_API_KEY:
    try:
        import streamlit as st
        DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        pass

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # V4-Flash: 最便宜模型

# 费用控制
MAX_BUDGET_YUAN = 80.0  # 最大预算（元）
# V4-Flash 定价: ¥1/百万输入token, ¥2/百万输出token
COST_PER_1K_INPUT = 0.001   # 输入: 1元/百万token
COST_PER_1K_OUTPUT = 0.002  # 输出: 2元/百万token

# 项目路径
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"
OUTPUT_DIR = BASE_DIR / "data" / "output"


@dataclass
class CostTracker:
    """API费用追踪器"""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    call_count: int = 0
    errors: int = 0

    def record(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += (
            input_tokens * COST_PER_1K_INPUT / 1000
            + output_tokens * COST_PER_1K_OUTPUT / 1000
        )
        self.call_count += 1

    def record_error(self):
        self.errors += 1

    @property
    def remaining_budget(self) -> float:
        return MAX_BUDGET_YUAN - self.total_cost

    def can_continue(self) -> bool:
        return self.remaining_budget > 1.0

    def summary(self) -> str:
        return (
            f"API调用: {self.call_count}次 | "
            f"输入: {self.total_input_tokens/1000:.1f}K tokens | "
            f"输出: {self.total_output_tokens/1000:.1f}K tokens | "
            f"已花费: {self.total_cost:.4f}元 | "
            f"剩余预算: {self.remaining_budget:.2f}元"
        )


# 全局费用追踪器
cost_tracker = CostTracker()
