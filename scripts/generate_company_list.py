"""生成全A股上市公司列表 — 用于批量ESG报告下载"""

import csv
from pathlib import Path

import akshare as ak

BASE_DIR = Path(__file__).parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "company_list.csv"


def get_exchange(code: str) -> tuple:
    """根据股票代码判断交易所"""
    prefix = code[0]
    if prefix == "6":
        return ("SSE", "沪市")
    return ("SZSE", "深市")


def main():
    print("正在获取全A股上市公司列表...")
    df = ak.stock_info_a_code_name()
    print(f"获取到 {len(df)} 家公司")

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name", "exchange", "market"])

        count = 0
        for _, row in df.iterrows():
            code = str(row["code"]).zfill(6)
            name = str(row["name"]).strip()
            exchange, market = get_exchange(code)
            writer.writerow([code, name, exchange, market])
            count += 1

    sse_count = 0
    szse_count = 0
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f2:
        for line in f2:
            if ",SSE," in line:
                sse_count += 1
            elif ",SZSE," in line:
                szse_count += 1
    print(f"已写入 {OUTPUT_PATH}，共 {count} 家公司")
    print(f"  沪市(SSE): {sse_count}")
    print(f"  深市(SZSE): {szse_count}")


if __name__ == "__main__":
    main()
