"""Agent工具定义 — Function Calling Schema + 执行分发器"""

import json
import logging
import traceback

logger = logging.getLogger(__name__)

# 将 schema 放在最前面方便修改
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_companies",
            "description": "列出所有可查询的上市公司名单。可按行业筛选。用户问'有哪些公司'、'金融行业有哪些公司'、'列出所有科技公司'时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "行业名称筛选，例如'金融'、'科技'、'医药'、'汽车'、'新能源'。不填则返回全部公司"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_indicators",
            "description": "查询ESG指标体系。用户问'有哪些环境指标'、'碳排放相关的有哪些'、'所有定量指标'时使用。返回指标ID、名称、类型、单位等信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "dimension": {
                        "type": "string",
                        "enum": ["E", "S", "G"],
                        "description": "维度筛选：E=环境, S=社会, G=治理"
                    },
                    "keyword": {
                        "type": "string",
                        "description": "指标名称或关键词搜索，例如'碳'、'排放'、'员工'、'研发'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_data",
            "description": "获取指定公司的全部ESG指标数据，包括定量指标（数值+单位）和定性指标（状态+摘要），以及该公司的ESG评分。用户问'比亚迪的ESG表现'、'美的集团的碳排放'、'某公司环境数据'时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司全称，如'比亚迪'、'美的集团'、'平安银行'、'万科A'"
                    },
                    "dimension": {
                        "type": "string",
                        "enum": ["E", "S", "G"],
                        "description": "可选，仅查询某维度数据。不填返回全部E/S/G"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_esg_scores",
            "description": "获取ESG综合评分及排名。用户问'ESG排名'、'哪些公司得分最高'、'某公司排第几'、'ESG得分'时使用。返回排名、E/S/G各维度得分和综合得分。",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "返回前N名，默认10。用户说'TOP5'时填5，'TOP20'时填20"
                    },
                    "company_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "指定公司名称列表，查询特定公司的评分排名。与top_n互斥"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_companies",
            "description": "对比多家公司在特定ESG指标上的数值。用户问'对比A和B的碳排放'、'哪家公司研发投入最高'、'对比几家公司的环保表现'时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要对比的公司全称列表，如['美的集团', '格力电器', '海尔智家']"
                    },
                    "indicator_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要对比的指标关键词，如['碳排放', '研发投入', '可再生能源']。不填则对比默认关键指标"
                    }
                },
                "required": ["company_names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_industry_analysis",
            "description": "获取行业层面的ESG对比分析数据，包括各行业的公司数量、平均碳排放、平均可再生比例、平均女性员工比例、平均研发占比等。用户问'各行业ESG对比'、'金融行业碳排放情况'、'哪个行业ESG表现好'时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "指定行业名称，如'金融'、'科技'。不填返回所有行业"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trend",
            "description": "查询某公司某ESG指标的数据变化趋势。用户问'比亚迪的碳排放这几年怎么变化'、'某公司用水量趋势'时使用。注意：当前数据以单年份为主，可能仅有单年数据。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司全称"
                    },
                    "indicator_keyword": {
                        "type": "string",
                        "description": "指标关键词，如'碳排放'、'用水'、'研发'、'女性员工'"
                    }
                },
                "required": ["company_name", "indicator_keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_overview",
            "description": "获取整体数据集概览：覆盖的公司数量、报告数量、行业分布、年份范围、数据质量概况等。用户问'数据概况'、'有多少家公司'、'覆盖哪些行业'时使用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]


def execute_tool(name: str, arguments: dict, adapter) -> str:
    """执行单个工具调用，返回JSON字符串结果

    Args:
        name: 工具名称
        arguments: 工具参数dict
        adapter: ESGDataAdapter实例

    Returns:
        JSON字符串，包含结果或错误信息
    """
    try:
        if name == "list_companies":
            result = adapter.get_companies(industry=arguments.get("industry"))

        elif name == "get_indicators":
            result = adapter.get_indicators(
                dimension=arguments.get("dimension"),
                keyword=arguments.get("keyword"),
            )

        elif name == "get_company_data":
            result = adapter.get_company_data(
                company_name=arguments.get("company_name", ""),
                dimension=arguments.get("dimension"),
            )

        elif name == "get_esg_scores":
            top_n = arguments.get("top_n", 10)
            company_names = arguments.get("company_names")
            result = adapter.get_esg_scores(top_n=top_n, company_names=company_names)

        elif name == "compare_companies":
            result = adapter.compare_companies(
                company_names=arguments.get("company_names", []),
                indicator_keywords=arguments.get("indicator_keywords"),
            )

        elif name == "get_industry_analysis":
            result = adapter.get_industry_analysis(industry=arguments.get("industry"))

        elif name == "get_trend":
            result = adapter.get_trend(
                company_name=arguments.get("company_name", ""),
                indicator_keyword=arguments.get("indicator_keyword", ""),
            )

        elif name == "get_data_overview":
            result = adapter.get_data_overview()

        else:
            result = {"error": f"未知工具: {name}"}

    except Exception as e:
        result = {"error": str(e), "traceback": traceback.format_exc()[-500:]}
        if hasattr(adapter, 'logger'):
            adapter.logger.error(f"工具执行失败 {name}: {e}")

    # 结果不应太大（限制token消耗）
    json_str = json.dumps(result, ensure_ascii=False, default=str)
    if len(json_str) > 8000:
        json_str = json_str[:8000] + '...\n[结果已截断]'
    return json_str

