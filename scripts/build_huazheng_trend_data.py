"""Build normalized Huazheng ESG quarterly trend data for the frontend.

Usage:
    python scripts/build_huazheng_trend_data.py --input "E:\\数据要素\\华证esg评级09.1-25.1（季度）.xlsx"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "analysis" / "huazheng_esg_quarterly.json"


def _value(row: pd.Series, column: str, default=None):
    value = row.get(column, default)
    if pd.isna(value):
        return default
    return value


def build_records(input_path: Path) -> list[dict]:
    df = pd.read_excel(input_path)
    required = {"证券代码", "季度日期", "证券简称", "综合得分", "E得分", "S得分", "G得分"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Excel缺少必要列: {', '.join(sorted(missing))}")

    df["季度日期"] = pd.to_datetime(df["季度日期"])
    df = df.sort_values(["证券代码", "季度日期"])

    records: list[dict] = []
    for _, row in df.iterrows():
        date = row["季度日期"]
        records.append(
            {
                "stock_code": str(int(row["证券代码"])).zfill(6),
                "company": str(_value(row, "证券简称", "")),
                "date": date.strftime("%Y-%m-%d"),
                "year": int(date.year),
                "quarter": f"Q{((date.month - 1) // 3) + 1}",
                "rating": _value(row, "综合评级", ""),
                "composite_score": float(_value(row, "综合得分", 0)),
                "e_rating": _value(row, "E评级", ""),
                "e_score": float(_value(row, "E得分", 0)),
                "s_rating": _value(row, "S评级", ""),
                "s_score": float(_value(row, "S得分", 0)),
                "g_rating": _value(row, "G评级", ""),
                "g_score": float(_value(row, "G得分", 0)),
                "industry_cs": _value(row, "证监会行业新", ""),
                "industry_ths": _value(row, "同花顺行业新", ""),
                "industry_sw": _value(row, "申万行业", ""),
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Huazheng ESG quarterly Excel to JSON trend data.")
    parser.add_argument("--input", required=True, help="Path to 华证ESG评级 Excel file.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    records = build_records(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(records, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    codes = {item["stock_code"] for item in records}
    print(f"wrote {len(records)} quarterly records for {len(codes)} companies -> {output_path}")


if __name__ == "__main__":
    main()
