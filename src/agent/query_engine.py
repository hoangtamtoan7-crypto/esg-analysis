"""ESG智能查询Agent — DeepSeek Function Calling 核心循环"""

import json
import logging
import os
import time

from src.extractor.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from src.agent.tools import TOOL_SCHEMAS, execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个专业的ESG（环境、社会和治理）数据分析助手，名为"ESG智能助手"。你可以查询和分析A股上市公司的ESG数据。

## 你的能力
- 查询52个ESG指标（31个定量 + 21个定性），覆盖环境(E)、社会(S)、治理(G)三个维度
- ESG综合评分排名分析
- 行业对比分析
- 公司间单一指标对比
- 指标趋势查询

## 回答规则
1. 用中文回答，语气专业但友好，适当使用Markdown格式化
2. 用户问及具体公司或指标时，务必先调用对应工具获取数据，不要凭记忆猜测
3. 数值问题给出具体数字和单位，标注数据年份来源
4. 数据不存在时直接告知"该数据暂未提取到"，绝不编造
5. 需要对比多公司时使用compare_companies工具
6. 需要排名时使用get_esg_scores工具
7. 当用户说的公司名不完整时（如"美的"），可以尝试调用工具，工具会自动返回模糊匹配建议
8. 非ESG相关问题，礼貌说明你的专业范围并引导用户提问ESG相关问题
9. 回答中可给出简短分析解读，但不要过度延伸

## 数据说明
- 来源：上市公司公开发布的ESG报告/可持续发展报告
- 通过DeepSeek大模型自动提取，置信度标注为high/medium/low
- 覆盖约110家A股上市公司"""


def format_ai_service_error(error: Exception | str) -> str:
    """Convert provider exceptions into user-facing, non-sensitive guidance."""
    raw = str(error)
    lowered = raw.lower()
    if "401" in raw or "authentication" in lowered or "invalid" in lowered:
        return (
            "抱歉，AI 服务认证失败：DeepSeek API Key 无效或已过期。\n\n"
            "请在 Streamlit Cloud 的 Manage app → Settings → Secrets 中更新 "
            "`DEEPSEEK_API_KEY`，保存后重启应用；本地运行则更新项目根目录的 `.env` 文件。"
        )
    if "timeout" in lowered or "timed out" in lowered:
        return "抱歉，AI 服务响应超时。请稍后重试，或把问题拆成更短的查询。"
    return "抱歉，AI 服务暂时不可用。请稍后重试，或检查 DeepSeek API 配置。"


class ESGQueryAgent:
    """ESG自然语言查询Agent"""

    def __init__(self, adapter):
        if not DEEPSEEK_API_KEY:
            raise ValueError("未设置DEEPSEEK_API_KEY环境变量")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("缺少 openai Python 包，请先安装 requirements.txt。") from exc
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        self.adapter = adapter
        self.tools = TOOL_SCHEMAS

    def query(self, user_message: str, chat_history: list = None) -> dict:
        """处理用户自然语言查询

        Args:
            user_message: 用户输入
            chat_history: 可选的历史消息列表

        Returns:
            {"text": str, "tool_calls_made": list}
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 只保留最近3轮对话（非tool消息）以控制上下文
        if chat_history:
            non_tool = [m for m in chat_history if m.get("role") != "tool"]
            recent = non_tool[-6:]  # 3 user + 3 assistant = 6 messages
            messages.extend(recent)

        messages.append({"role": "user", "content": user_message})

        tool_calls_made = []
        max_iterations = 5
        start_time = time.time()
        QUERY_TIMEOUT = 60

        for iteration in range(max_iterations):
            if time.time() - start_time > QUERY_TIMEOUT:
                return {
                    "text": "抱歉，查询超时。请尝试简化您的问题。",
                    "tool_calls_made": tool_calls_made,
                }

            try:
                response = self.client.chat.completions.create(
                    model=DEEPSEEK_MODEL,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=2048,
                    timeout=30,
                )
            except Exception as e:
                logger.error(f"DeepSeek API调用失败: {e}")
                return {
                    "text": format_ai_service_error(e),
                    "tool_calls_made": tool_calls_made,
                }

            msg = response.choices[0].message

            if msg.tool_calls:
                # 追加assistant消息（含tool_calls）
                messages.append(msg.model_dump())

                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    tool_result = execute_tool(tool_name, tool_args, self.adapter)
                    tool_calls_made.append((tool_name, tool_args))

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result,
                    })
            else:
                # 最终文本回答
                return {
                    "text": msg.content or "抱歉，未能生成回答。请换个方式提问。",
                    "tool_calls_made": tool_calls_made,
                }

        # 达到最大迭代次数
        return {
            "text": "抱歉，查询处理超时。请尝试简化问题或分步提问。",
            "tool_calls_made": tool_calls_made,
        }


def create_agent(adapter) -> ESGQueryAgent:
    """工厂函数：创建Agent实例"""
    if not DEEPSEEK_API_KEY:
        return None
    try:
        return ESGQueryAgent(adapter)
    except Exception as e:
        logger.error(f"创建Agent失败: {e}")
        return None

