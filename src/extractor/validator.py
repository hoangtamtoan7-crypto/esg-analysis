"""结果校验器

对LLM提取的ESG指标结果进行多维度校验：
1. 数值合理性检查
2. 单位一致性验证
3. 必填字段检查
4. 置信度评估
"""

import logging
from typing import List, Tuple

from .indicators import get_indicator_by_id, ALL_INDICATORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class ESGValidator:
    """ESG提取结果校验器"""

    # 合理性范围（防止明显错误）
    REASONABLE_RANGES = {
        "E_Q01": (0, 1_000_000_000),     # 碳排放: 0 ~ 10亿吨
        "E_Q02": (0, 1_000_000_000),
        "E_Q03": (0, 1_000_000_000),
        "E_Q05": (0, 1_000_000_000),     # 能耗: 0 ~ 10亿MWh
        "E_Q06": (0, 100),               # 可再生能源比例: 0-100%
        "E_Q07": (0, 1_000_000_000),     # 用水: 0 ~ 10亿吨
        "S_Q01": (10, 10_000_000),       # 员工: 10 ~ 1000万
        "S_Q02": (0, 100),               # 女性比例: 0-100%
        "S_Q03": (0, 100),
        "S_Q04": (0, 1_000_000_000),     # 培训投入: 0 ~ 100亿
        "S_Q06": (0, 100),               # 流失率: 0-100%
        "S_Q10": (0, 100),               # 工伤率: 0-100‰
        "G_Q01": (3, 50),                # 董事会: 3-50人
        "G_Q02": (0, 100),               # 独董比例: 0-100%
        "G_Q04": (1, 100),               # 董事会会议: 1-100次
    }

    # 常见单位映射（统一标准化）
    UNIT_ALIASES = {
        "吨二氧化碳当量": "tCO2e",
        "万吨二氧化碳当量": "万tCO2e",
        "吨CO2e": "tCO2e",
        "万千瓦时": "万kWh",
        "兆瓦时": "MWh",
        "吉瓦时": "GWh",
        "度": "kWh",
        "人": "人",
        "万元": "万元",
        "亿元": "亿元",
        "%": "%",
        "小时": "小时",
        "次": "次",
        "吨": "吨",
        "万吨": "万吨",
    }

    def validate(self, extraction_result: dict) -> dict:
        """校验提取结果

        Returns:
            {
                "is_valid": bool,
                "quantitative_valid": int,
                "quantitative_issues": [...],
                "qualitative_valid": int,
                "qualitative_issues": [...],
                "overall_quality_score": float,
            }
        """
        issues = {
            "quantitative": [],
            "qualitative": [],
        }

        qt_indicators = extraction_result.get("quantitative_indicators", [])
        ql_indicators = extraction_result.get("qualitative_indicators", [])

        for item in qt_indicators:
            item_issues = self._validate_quantitative(item)
            if item_issues:
                for issue in item_issues:
                    issues["quantitative"].append({
                        "indicator_id": item.get("id"),
                        "indicator_name": item.get("name"),
                        "issue": issue,
                    })

        for item in ql_indicators:
            item_issues = self._validate_qualitative(item)
            if item_issues:
                for issue in item_issues:
                    issues["qualitative"].append({
                        "indicator_id": item.get("id"),
                        "indicator_name": item.get("name"),
                        "issue": issue,
                    })

        qt_total = len(qt_indicators)
        ql_total = len(ql_indicators)
        qt_valid = qt_total - len(issues["quantitative"])
        ql_valid = ql_total - len(issues["qualitative"])

        # 质量分
        covered_count = sum(
            1 for item in qt_indicators + ql_indicators
            if item.get("value") is not None or item.get("status")
        )
        quality_score = min(
            1.0,
            (covered_count / max(len(ALL_INDICATORS), 1)) * 0.5
            + (qt_valid / max(qt_total, 1)) * 0.25
            + (ql_valid / max(ql_total, 1)) * 0.25,
        )

        return {
            "is_valid": len(issues["quantitative"]) + len(issues["qualitative"]) == 0,
            "quantitative_count": qt_total,
            "quantitative_valid": qt_valid,
            "quantitative_issues": issues["quantitative"],
            "qualitative_count": ql_total,
            "qualitative_valid": ql_valid,
            "qualitative_issues": issues["qualitative"],
            "overall_quality_score": round(quality_score, 3),
        }

    def _validate_quantitative(self, item: dict) -> List[str]:
        """校验单个定量指标"""
        issues = []

        ind_id = item.get("id", "")
        if not ind_id:
            issues.append("缺少指标ID")
            return issues

        # 检查必填字段
        for field in ["name", "value", "unit"]:
            if field not in item:
                issues.append(f"缺少必填字段: {field}")

        value = item.get("value")
        if value is not None:
            # 检查数值类型
            if not isinstance(value, (int, float)):
                issues.append(f"value类型错误: {type(value).__name__}")

            # 检查数值范围
            if ind_id in self.REASONABLE_RANGES:
                lo, hi = self.REASONABLE_RANGES[ind_id]
                if isinstance(value, (int, float)) and (value < lo or value > hi):
                    issues.append(f"数值{value}超出合理范围[{lo}, {hi}]")

        return issues

    def _validate_qualitative(self, item: dict) -> List[str]:
        """校验单个定性指标"""
        issues = []

        ind_id = item.get("id", "")
        if not ind_id:
            issues.append("缺少指标ID")
            return issues

        status = item.get("status", "")
        if status and status not in ("yes", "no", "partial"):
            issues.append(f"status值无效: {status}（应为yes/no/partial）")

        if "summary" not in item:
            issues.append("缺少summary字段")

        return issues

    def normalize_units(self, extraction_result: dict) -> dict:
        """标准化单位名称"""
        for item in extraction_result.get("quantitative_indicators", []):
            unit = item.get("unit", "")
            if unit in self.UNIT_ALIASES:
                item["unit_normalized"] = self.UNIT_ALIASES[unit]
            else:
                item["unit_normalized"] = unit
        return extraction_result

    def check_completeness(self, extraction_result: dict) -> dict:
        """检查指标覆盖完整度"""
        extracted_ids = set()
        for item in extraction_result.get("quantitative_indicators", []):
            extracted_ids.add(item.get("id"))
        for item in extraction_result.get("qualitative_indicators", []):
            extracted_ids.add(item.get("id"))

        missing = []
        for ind in ALL_INDICATORS:
            if ind.id not in extracted_ids:
                missing.append({"id": ind.id, "name": ind.name, "type": ind.indicator_type})

        return {
            "total_indicators": len(ALL_INDICATORS),
            "extracted": len(extracted_ids),
            "missing": len(missing),
            "missing_list": missing,
            "completeness": round(len(extracted_ids) / len(ALL_INDICATORS) * 100, 1),
        }
