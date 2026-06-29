"""Helpers for Streamlit-facing ESG data cleaning and quality summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.analyzer import classify_industry
from src.extractor.indicators import ALL_INDICATORS
from src.extractor.validator import ESGValidator


INDICATOR_BY_ID = {indicator.id: indicator for indicator in ALL_INDICATORS}
LOW_SIGNAL_NAME_MARKERS = ("ST", "*ST", "退")


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def is_valid_quantitative(item: dict) -> bool:
    """Return True when a quantitative item contains a real numeric value."""
    return isinstance(item.get("value"), (int, float))


def is_valid_qualitative(item: dict) -> bool:
    """Return True when a qualitative item carries positive or useful evidence."""
    status = (item.get("status") or "").strip().lower()
    text = f"{item.get('summary') or ''}{item.get('original_text') or ''}".strip()
    return status in {"yes", "partial"} or (bool(text) and status != "no")


def count_valid_indicators(result: dict) -> dict:
    quantitative = sum(
        1 for item in result.get("quantitative_indicators", [])
        if is_valid_quantitative(item)
    )
    qualitative = sum(
        1 for item in result.get("qualitative_indicators", [])
        if is_valid_qualitative(item)
    )
    return {
        "quantitative": quantitative,
        "qualitative": qualitative,
        "total": quantitative + qualitative,
    }


def build_industry_coverage(results: list[dict]) -> list[dict]:
    """Build industry coverage stats from result objects, with name-based fallback."""
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"companies": set(), "reports": 0, "quality_scores": [], "coverages": []}
    )

    for result in results:
        company = result.get("company_name") or ""
        if not company:
            continue
        industry = result.get("industry") or classify_industry(company)
        bucket = grouped[industry]
        bucket["companies"].add(company)
        bucket["reports"] += 1
        bucket["quality_scores"].append(
            _to_float(result.get("validation", {}).get("overall_quality_score"))
        )
        bucket["coverages"].append(
            _to_float(result.get("completeness", {}).get("completeness"))
        )

    rows = []
    for industry, bucket in grouped.items():
        quality_scores = bucket["quality_scores"]
        coverages = bucket["coverages"]
        rows.append({
            "行业": industry,
            "公司数": len(bucket["companies"]),
            "报告数": bucket["reports"],
            "平均质量分": round(sum(quality_scores) / max(len(quality_scores), 1), 3),
            "平均覆盖度": round(sum(coverages) / max(len(coverages), 1), 1),
        })

    return sorted(rows, key=lambda row: (-row["报告数"], -row["公司数"], row["行业"]))


def is_low_signal_company(name: str) -> bool:
    normalized = (name or "").upper()
    return any(marker in normalized for marker in LOW_SIGNAL_NAME_MARKERS)


def filter_company_options(
    results: list[dict],
    *,
    include_low_signal: bool = False,
    min_valid_indicators: int = 3,
) -> list[dict]:
    """Return sorted company options, hiding low-signal samples by default."""
    options = []
    for result in results:
        company = result.get("company_name") or ""
        if not company:
            continue
        counts = count_valid_indicators(result)
        validation = result.get("validation", {})
        completeness = result.get("completeness", {})
        low_signal = is_low_signal_company(company) or counts["total"] < min_valid_indicators
        if low_signal and not include_low_signal:
            continue
        options.append({
            "company": company,
            "year": str(result.get("report_year", "")),
            "result": result,
            "valid_quantitative": counts["quantitative"],
            "valid_qualitative": counts["qualitative"],
            "valid_total": counts["total"],
            "quality_score": _to_float(validation.get("overall_quality_score")),
            "coverage": _to_float(completeness.get("completeness")),
            "low_signal": low_signal,
        })

    return sorted(
        options,
        key=lambda row: (
            row["low_signal"],
            -row["valid_total"],
            -row["quality_score"],
            -row["coverage"],
            row["company"],
        ),
    )


def _indicator_name(indicator_id: str, fallback: str = "") -> str:
    indicator = INDICATOR_BY_ID.get(indicator_id)
    return indicator.name if indicator else (fallback or indicator_id)


def _issue_suggestion(issue: str) -> str:
    if "缺失定量数值" in issue or "value" in issue:
        return "复核原报告表格或文本，无法确认时不纳入数值对比。"
    if "缺失定性判断" in issue or "summary" in issue:
        return "补充政策/制度/行动描述，或标记为未披露。"
    if "范围" in issue:
        return "核对单位换算和数量级，必要时回看原文。"
    return "回看原文证据并更新抽取字段。"


def build_validation_detail(result: dict) -> dict:
    """Return concrete validation rows and completeness details for one report."""
    validator = ESGValidator()
    validation = validator.validate(result)
    completeness = validator.check_completeness(result)
    issues = []

    for item in result.get("quantitative_indicators", []):
        if not is_valid_quantitative(item):
            issue = "缺失定量数值"
            issues.append({
                "指标ID": item.get("id", ""),
                "指标名称": _indicator_name(item.get("id", ""), item.get("name", "")),
                "问题类型": issue,
                "原值/状态": item.get("value"),
                "单位": item.get("unit", ""),
                "建议处理": _issue_suggestion(issue),
            })

    for item in result.get("qualitative_indicators", []):
        if not is_valid_qualitative(item):
            issue = "缺失定性判断"
            issues.append({
                "指标ID": item.get("id", ""),
                "指标名称": _indicator_name(item.get("id", ""), item.get("name", "")),
                "问题类型": issue,
                "原值/状态": item.get("status", ""),
                "单位": "",
                "建议处理": _issue_suggestion(issue),
            })

    for issue in validation.get("quantitative_issues", []):
        issue_text = issue.get("issue", "")
        issues.append({
            "指标ID": issue.get("indicator_id", ""),
            "指标名称": _indicator_name(
                issue.get("indicator_id", ""), issue.get("indicator_name", "")
            ),
            "问题类型": issue_text,
            "原值/状态": "",
            "单位": "",
            "建议处理": _issue_suggestion(issue_text),
        })

    for issue in validation.get("qualitative_issues", []):
        issue_text = issue.get("issue", "")
        issues.append({
            "指标ID": issue.get("indicator_id", ""),
            "指标名称": _indicator_name(
                issue.get("indicator_id", ""), issue.get("indicator_name", "")
            ),
            "问题类型": issue_text,
            "原值/状态": "",
            "单位": "",
            "建议处理": _issue_suggestion(issue_text),
        })

    missing = [
        {
            "指标ID": item.get("id", ""),
            "指标名称": item.get("name", ""),
            "类型": "定量" if item.get("type") == "quantitative" else "定性",
        }
        for item in completeness.get("missing_list", [])
    ]
    counts = count_valid_indicators(result)

    return {
        "summary": {
            "quantitative_valid": counts["quantitative"],
            "qualitative_valid": counts["qualitative"],
            "missing_value_count": len(issues),
            "missing_indicator_count": completeness.get("missing", 0),
            "completeness": completeness.get("completeness", 0),
            "quality_score": validation.get("overall_quality_score", 0),
        },
        "issues": issues,
        "missing": missing,
        "validation": validation,
        "completeness": completeness,
    }
