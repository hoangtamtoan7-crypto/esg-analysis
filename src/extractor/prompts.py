"""Prompt模板

为ESG指标提取设计结构化Prompt，包含：
1. 系统指令 - 定义角色和输出格式
2. Few-shot示例 - 帮助模型理解任务
3. 指标体系 - 需要提取的指标列表
"""

from .indicators import (
    ALL_INDICATORS, QUANTITATIVE_INDICATORS, QUALITATIVE_INDICATORS,
    INDICATORS_BY_DIMENSION,
)


def build_system_prompt() -> str:
    """构建系统指令"""
    return """你是一名专业的ESG（环境、社会和治理）数据分析师。你的任务是从上市公司ESG报告中精确提取关键指标。

## 核心要求

1. **定量指标**: 提取具体数值、单位、年份。如果报告未提及，字段留空(null)，不要编造数据。
2. **定性指标**: 提取原文关键描述（不超过200字），判断企业是否有相关政策/措施（yes/no/partial）。
3. **引用原文**: 尽可能提供原文出处，方便人工校验。
4. **注意单位**: 不同公司可能使用不同单位（如碳排放用"吨"或"万吨"），请原样提取并标注单位。

## 输出格式

请严格按JSON格式输出，包含以下字段：
- company_name: 公司名称
- report_year: 报告年度
- quantitative_indicators: 定量指标列表
- qualitative_indicators: 定性指标列表

每个定量指标格式：
{
  "id": "指标ID",
  "name": "指标名称",
  "value": 数值(纯数字)或null,
  "unit": "单位",
  "original_text": "原文片段",
  "confidence": "high/medium/low"
}

每个定性指标格式：
{
  "id": "指标ID",
  "name": "指标名称",
  "status": "yes/no/partial",
  "summary": "原文描述摘要(不超过200字)",
  "original_text": "原文关键片段",
  "confidence": "high/medium/low"
}

## 重要提醒
- 只提取客观存在的数据，不推断、不猜测
- 找不到的数据将value设为null，status留空
- 注意区分不同范围（如范围1/范围2排放）
- 表格中的数据也要仔细提取"""


def build_extraction_prompt(indicators: list = None) -> str:
    """构建单次提取的用户提示

    Args:
        indicators: 要提取的指标列表，默认全部
    """
    if indicators is None:
        indicators = ALL_INDICATORS

    lines = ["请从以下ESG报告内容中提取指定指标。\n"]

    lines.append("## 需要提取的定量指标：")
    for ind in indicators:
        if ind.indicator_type == "quantitative":
            lines.append(
                f"- [{ind.id}] {ind.name}"
                f"{' (单位: ' + ind.unit + ')' if ind.unit else ''}"
                f" 关键词: {'/'.join(ind.keywords[:5])}"
            )

    lines.append("\n## 需要提取的定性指标：")
    for ind in indicators:
        if ind.indicator_type == "qualitative":
            lines.append(
                f"- [{ind.id}] {ind.name}"
                f" 关键词: {'/'.join(ind.keywords[:5])}"
            )

    lines.append("\n## ESG报告内容：")
    lines.append("{report_chunk}")

    lines.append("\n请按JSON格式输出提取结果。")

    return "\n".join(lines)


def build_dimension_prompt(dimension: str) -> str:
    """为单个维度构建提取提示（减少单次token消耗）

    Args:
        dimension: "E" / "S" / "G"
    """
    indicators = INDICATORS_BY_DIMENSION.get(dimension, [])
    dim_name = {"E": "环境", "S": "社会", "G": "治理"}.get(dimension, dimension)

    lines = [f"请从以下ESG报告内容中提取**{dim_name}维度**的指标。\n"]

    lines.append("## 定量指标：")
    for ind in indicators:
        if ind.indicator_type == "quantitative":
            lines.append(f"- [{ind.id}] {ind.name} ({ind.unit or '无固定单位'})")

    lines.append("\n## 定性指标：")
    for ind in indicators:
        if ind.indicator_type == "qualitative":
            lines.append(f"- [{ind.id}] {ind.name}")

    lines.append("\n## ESG报告内容：")
    lines.append("{report_chunk}")
    lines.append("\n请按JSON格式输出提取结果，只提取上述列出的指标。")

    return "\n".join(lines)


def build_combined_prompt() -> str:
    """构建全维度合并提取提示（单次API调用提取E+S+G，降低费用）"""
    lines = ["请从以下ESG报告内容中提取所有维度的指标。\n"]

    for dim, dim_name in [("E", "环境"), ("S", "社会"), ("G", "治理")]:
        indicators = INDICATORS_BY_DIMENSION.get(dim, [])
        lines.append(f"## {dim_name}维度")

        qt = [ind for ind in indicators if ind.indicator_type == "quantitative"]
        if qt:
            lines.append("定量指标：")
            for ind in qt:
                lines.append(f"- [{ind.id}] {ind.name} ({ind.unit or '无固定单位'})")

        ql = [ind for ind in indicators if ind.indicator_type == "qualitative"]
        if ql:
            lines.append("定性指标：")
            for ind in ql:
                lines.append(f"- [{ind.id}] {ind.name}")
        lines.append("")

    lines.append("## ESG报告内容：")
    lines.append("{report_chunk}")
    lines.append("\n请按JSON格式输出所有提取结果（包含quantitative_indicators和qualitative_indicators）。只提取上述列出的指标。")

    return "\n".join(lines)


def build_keyword_match_prompt(indicator, report_chunk: str) -> str:
    """针对单个指标的精准提取提示"""
    return f"""请从以下ESG报告片段中提取指标"{indicator.name}"（ID: {indicator.id}）。

指标类型: {'定量(需提取数值和单位)' if indicator.indicator_type == 'quantitative' else '定性(需判断有/无并摘要)'}
关键词: {', '.join(indicator.keywords)}
{'单位参考: ' + indicator.unit if indicator.unit else ''}

报告内容：
{report_chunk}

请以JSON格式返回该单个指标的提取结果。"""


# Few-shot 示例（帮助模型理解任务）
FEW_SHOT_EXAMPLE_QUANTITATIVE = """
示例 - 定量指标提取：

报告原文："2024年度，公司温室气体排放总量为125.6万吨二氧化碳当量，其中范围1排放35.2万吨，范围2排放90.4万吨。综合能源消耗3,200兆瓦时。"

提取结果：
{
  "quantitative_indicators": [
    {"id": "E_Q01", "name": "温室气体排放总量", "value": 1256000, "unit": "吨二氧化碳当量", "original_text": "温室气体排放总量为125.6万吨二氧化碳当量", "confidence": "high"},
    {"id": "E_Q02", "name": "范围1排放", "value": 352000, "unit": "吨二氧化碳当量", "original_text": "范围1排放35.2万吨", "confidence": "high"},
    {"id": "E_Q03", "name": "范围2排放", "value": 904000, "unit": "吨二氧化碳当量", "original_text": "范围2排放90.4万吨", "confidence": "high"},
    {"id": "E_Q05", "name": "综合能源消耗", "value": 3200, "unit": "兆瓦时", "original_text": "综合能源消耗3,200兆瓦时", "confidence": "high"}
  ]
}
"""

FEW_SHOT_EXAMPLE_QUALITATIVE = """
示例 - 定性指标提取：

报告原文："公司已建立完善的环境管理体系，通过了ISO 14001:2015认证。2024年，公司制定了碳中和路线图，目标是2030年碳达峰、2060年碳中和。"

提取结果：
{
  "qualitative_indicators": [
    {"id": "E_L01", "name": "气候变化应对策略", "status": "yes", "summary": "公司已制定碳中和路线图，目标2030年碳达峰、2060年碳中和。", "original_text": "制定了碳中和路线图，目标是2030年碳达峰、2060年碳中和", "confidence": "high"},
    {"id": "E_L02", "name": "环境管理体系", "status": "yes", "summary": "已通过ISO 14001:2015环境管理体系认证。", "original_text": "通过了ISO 14001:2015认证", "confidence": "high"}
  ]
}
"""
