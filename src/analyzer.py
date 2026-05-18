"""ESG数据分析引擎

基于提取结果进行行业对比、公司排名、数据洞察。
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"

# 行业分类（基于公司名称关键词映射）
INDUSTRY_MAP = [
    # 金融
    ("银行", "金融"), ("保险", "金融"), ("证券", "金融"), ("太保", "金融"),
    ("财富", "金融"), ("华泰", "金融"), ("同花顺", "金融"),
    # 食品饮料
    ("茅台", "食品饮料"), ("五粮液", "食品饮料"), ("老窖", "食品饮料"),
    ("汾酒", "食品饮料"), ("洋河", "食品饮料"), ("古井", "食品饮料"),
    ("伊利", "食品饮料"), ("海天", "食品饮料"), ("双汇", "食品饮料"),
    ("啤酒", "食品饮料"),
    # 医药
    ("医药", "医药"), ("制药", "医药"), ("医疗", "医药"), ("药明", "医药"),
    ("爱尔", "医药"), ("白药", "医药"), ("片仔", "医药"),
    ("泰格", "医药"), ("康龙", "医药"), ("智飞", "医药"),
    # 能源
    ("石油", "能源"), ("石化", "能源"), ("煤炭", "能源"), ("神华", "能源"),
    ("电力", "能源"), ("核电", "能源"), ("能源", "能源"), ("煤业", "能源"),
    ("兖矿", "能源"), ("华能", "能源"),
    # 科技/电子
    ("科技", "科技"), ("海康", "科技"), ("大华", "科技"), ("讯飞", "科技"),
    ("金山", "科技"), ("京东方", "科技"), ("紫光", "科技"), ("立讯", "科技"),
    ("蓝思", "科技"), ("圣邦", "科技"), ("卓胜", "科技"), ("兆易", "科技"),
    ("中微", "科技"), ("北方华创", "科技"), ("三环", "科技"),
    ("汇川", "科技"), ("国电南瑞", "科技"),
    ("TCL", "科技"), ("中兴", "科技"), ("传音", "科技"), ("中芯", "科技"),
    # 汽车
    ("比亚迪", "汽车"), ("上汽", "汽车"), ("长安汽车", "汽车"),
    ("广汽", "汽车"), ("福耀", "汽车"),
    # 制造业
    ("美的", "制造业"), ("格力", "制造业"), ("海尔", "制造业"),
    ("重工", "制造业"), ("三一", "制造业"), ("潍柴", "制造业"),
    ("船舶", "制造业"), ("航发", "制造业"),
    # 材料
    ("钢铁", "材料"), ("钢股份", "材料"), ("特钢", "材料"), ("水泥", "材料"),
    ("化学", "材料"), ("万华", "材料"), ("建材", "材料"), ("雨虹", "材料"),
    # 房地产
    ("万科", "房地产"), ("招商蛇口", "房地产"), ("保利", "房地产"),
    ("中国建筑", "建筑"),
    # 交通运输
    ("航空", "交通运输"), ("国航", "交通运输"), ("东航", "交通运输"),
    ("南航", "交通运输"), ("机场", "交通运输"), ("铁路", "交通运输"),
    ("顺丰", "交通运输"), ("远洋", "交通运输"), ("中远海控", "交通运输"),
    # 新能源
    ("隆基", "新能源"), ("阳光电源", "新能源"), ("通威", "新能源"),
    ("中环", "新能源"), ("赣锋", "新能源"), ("宁德时代", "新能源"),
    # 农业
    ("牧原", "农业"), ("温氏", "农业"), ("海大", "农业"),
    # 传媒
    ("分众", "传媒"), ("芒果", "传媒"),
    # 通信
    ("电信", "通信"), ("联通", "通信"), ("移动", "通信"),
]

# E维度合理方向：值越小越好
E_LOWER_IS_BETTER = {"E_Q01", "E_Q02", "E_Q03", "E_Q04", "E_Q07", "E_Q08", "E_Q09", "E_Q11", "E_Q12", "E_Q13"}
# E维度合理方向：值越大越好
E_HIGHER_IS_BETTER = {"E_Q06", "E_Q10"}


def classify_industry(name: str) -> str:
    for kw, ind in INDUSTRY_MAP:
        if kw in name:
            return ind
    return "其他"


def load_clean_data() -> pd.DataFrame:
    """加载清洗后的数据"""
    rows = []
    for f in sorted(OUTPUT_DIR.glob("*_result.json")):
        with open(f, "r", encoding="utf-8") as fp:
            r = json.load(fp)
        company = r.get("company_name", "")
        year = r.get("report_year", "")
        validation = r.get("validation", {})
        completeness = r.get("completeness", {})

        # 跳过空报告
        if completeness.get("completeness", 0) == 0:
            continue

        industry = classify_industry(company)
        quality = validation.get("overall_quality_score", 0)
        coverage = completeness.get("completeness", 0)

        for item in r.get("quantitative_indicators", []):
            val = item.get("value")
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                continue
            rows.append({
                "公司": company,
                "行业": industry,
                "年份": year,
                "指标ID": item.get("id"),
                "指标名称": item.get("name"),
                "数值": val,
                "单位": item.get("unit"),
                "置信度": item.get("confidence", ""),
                "质量分": quality,
                "覆盖度": coverage,
            })

    return pd.DataFrame(rows)


def compute_esg_scores(df: pd.DataFrame) -> pd.DataFrame:
    """计算ESG综合得分

    E维度：碳排放/能耗越低越好，可再生比例越高越好
    S维度：培训投入、研发投入越高越好，事故率越低越好
    G维度：独立董事比例越高越好
    """
    # 按公司汇总
    companies = []
    for name, group in df.groupby("公司"):
        scores = {"公司": name, "行业": group["行业"].iloc[0]}

        # E维度：碳排放强度（取排放强度或总量/营收≈强度）
        e_items = group[group["指标ID"].str.startswith("E_")]
        e_score = 0
        e_count = 0

        # 温室气体排放总量（越低越好→归一化取反）
        ghg = e_items[e_items["指标ID"] == "E_Q01"]["数值"]
        if len(ghg) > 0 and ghg.iloc[0] > 0:
            e_score += 1  # 有披露即加分
            e_count += 1

        renewable = e_items[e_items["指标ID"] == "E_Q06"]["数值"]
        if len(renewable) > 0:
            e_score += min(renewable.iloc[0] / 100, 1)
            e_count += 1

        env_invest = e_items[e_items["指标ID"] == "E_Q10"]["数值"]
        if len(env_invest) > 0 and env_invest.iloc[0] > 0:
            e_score += 1
            e_count += 1

        scores["E_得分"] = round(e_score / max(e_count, 1), 3)

        # S维度
        s_items = group[group["指标ID"].str.startswith("S_")]
        s_score = 0
        s_count = 0

        training_hours = s_items[s_items["指标ID"] == "S_Q05"]["数值"]
        if len(training_hours) > 0:
            s_score += min(training_hours.iloc[0] / 100, 1)
            s_count += 1

        rd_ratio = s_items[s_items["指标ID"] == "S_Q08"]["数值"]
        if len(rd_ratio) > 0:
            s_score += min(rd_ratio.iloc[0] / 20, 1)
            s_count += 1

        female_ratio = s_items[s_items["指标ID"] == "S_Q02"]["数值"]
        if len(female_ratio) > 0:
            s_score += min(female_ratio.iloc[0] / 50, 1)
            s_count += 1

        scores["S_得分"] = round(s_score / max(s_count, 1), 3)

        # G维度
        g_items = group[group["指标ID"].str.startswith("G_")]
        g_score = 0
        g_count = 0

        indep_ratio = g_items[g_items["指标ID"] == "G_Q02"]["数值"]
        if len(indep_ratio) > 0:
            g_score += min(indep_ratio.iloc[0] / 50, 1)
            g_count += 1

        board_meetings = g_items[g_items["指标ID"] == "G_Q04"]["数值"]
        if len(board_meetings) > 0:
            g_score += min(board_meetings.iloc[0] / 12, 1)
            g_count += 1

        scores["G_得分"] = round(g_score / max(g_count, 1), 3)

        # 综合得分
        scores["ESG综合"] = round((scores["E_得分"] + scores["S_得分"] + scores["G_得分"]) / 3, 3)
        companies.append(scores)

    result = pd.DataFrame(companies)
    result = result.sort_values("ESG综合", ascending=False).reset_index(drop=True)
    result["排名"] = range(1, len(result) + 1)
    return result[["排名", "公司", "行业", "E_得分", "S_得分", "G_得分", "ESG综合"]]


def industry_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """按行业汇总分析"""
    industries = []
    for name, group in df.groupby("行业"):
        e_q01 = group[group["指标ID"] == "E_Q01"]["数值"]
        e_q06 = group[group["指标ID"] == "E_Q06"]["数值"]
        s_q02 = group[group["指标ID"] == "S_Q02"]["数值"]
        s_q08 = group[group["指标ID"] == "S_Q08"]["数值"]

        industries.append({
            "行业": name,
            "公司数": group["公司"].nunique(),
            "平均碳排放(吨)": round(e_q01.mean(), 0) if len(e_q01) > 0 else None,
            "平均可再生比例(%)": round(e_q06.mean(), 1) if len(e_q06) > 0 else None,
            "平均女性员工(%)": round(s_q02.mean(), 1) if len(s_q02) > 0 else None,
            "平均研发占比(%)": round(s_q08.mean(), 2) if len(s_q08) > 0 else None,
        })

    return pd.DataFrame(industries).sort_values("公司数", ascending=False)


def generate_insights(df: pd.DataFrame) -> list:
    """生成数据洞察"""
    insights = []

    # 1. 碳排放
    ghg = df[df["指标ID"] == "E_Q01"].dropna(subset=["数值"])
    if len(ghg) > 0:
        top_ghg = ghg.nlargest(3, "数值")
        low_ghg = ghg.nsmallest(3, "数值")
        insights.append({
            "类别": "环境",
            "洞察": f"碳排放最高: {', '.join(f'{r.公司}({r.数值:,.0f}吨)' for _,r in top_ghg.iterrows())}",
        })

    # 2. 可再生能源
    renewable = df[df["指标ID"] == "E_Q06"].dropna(subset=["数值"])
    if len(renewable) > 0:
        high_re = renewable.nlargest(3, "数值")
        insights.append({
            "类别": "环境",
            "洞察": f"可再生能源比例最高: {', '.join(f'{r.公司}({r.数值:.1f}%)' for _,r in high_re.iterrows())}",
        })

    # 3. 研发
    rd = df[df["指标ID"] == "S_Q08"].dropna(subset=["数值"])
    if len(rd) > 0:
        top_rd = rd.nlargest(3, "数值")
        insights.append({
            "类别": "社会",
            "洞察": f"研发投入占比最高: {', '.join(f'{r.公司}({r.数值:.2f}%)' for _,r in top_rd.iterrows())}",
        })

    # 4. 女性员工
    female = df[df["指标ID"] == "S_Q02"].dropna(subset=["数值"])
    if len(female) > 0:
        high_f = female.nlargest(3, "数值")
        insights.append({
            "类别": "社会",
            "洞察": f"女性员工比例最高: {', '.join(f'{r.公司}({r.数值:.1f}%)' for _,r in high_f.iterrows())}",
        })

    # 5. 独立董事
    indep = df[df["指标ID"] == "G_Q02"].dropna(subset=["数值"])
    if len(indep) > 0:
        avg_indep = indep["数值"].mean()
        insights.append({
            "类别": "治理",
            "洞察": f"独立董事比例均值: {avg_indep:.1f}%, 共{len(indep)}家公司披露",
        })

    # 6. 数据覆盖度
    quality_scores = df.groupby("公司")["质量分"].mean()
    insights.append({
        "类别": "数据质量",
        "洞察": f"平均质量分: {quality_scores.mean():.3f}, 最高: {quality_scores.max():.3f}",
    })

    # 7. 行业覆盖
    industries = df["行业"].nunique()
    companies = df["公司"].nunique()
    insights.append({
        "类别": "总体",
        "洞察": f"覆盖{industries}个行业、{companies}家A股上市公司",
    })

    return insights


def run_full_analysis() -> dict:
    """运行完整分析"""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("加载数据...")
    df = load_clean_data()
    logger.info(f"数据加载完成: {len(df)}行, {df['公司'].nunique()}家公司, {df['行业'].nunique()}个行业")

    # ESG评分
    scores = compute_esg_scores(df)
    logger.info(f"ESG评分TOP5:\n{scores.head(5).to_string()}")

    # 行业分析
    industries = industry_analysis(df)

    # 洞察
    insights = generate_insights(df)

    # 保存结果
    scores.to_csv(ANALYSIS_DIR / "esg_scores.csv", index=False, encoding="utf-8-sig")
    industries.to_csv(ANALYSIS_DIR / "industry_analysis.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(insights).to_csv(ANALYSIS_DIR / "insights.csv", index=False, encoding="utf-8-sig")

    # 生成分析报告Markdown
    report = _generate_report(scores, industries, insights, df)
    report_path = ANALYSIS_DIR / "analysis_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"分析完成，报告已保存到: {report_path}")
    logger.info(f"ESG评分: {ANALYSIS_DIR / 'esg_scores.csv'}")
    logger.info(f"行业分析: {ANALYSIS_DIR / 'industry_analysis.csv'}")

    return {
        "scores": scores,
        "industries": industries,
        "insights": insights,
        "report_path": str(report_path),
    }


def _generate_report(scores, industries, insights, df) -> str:
    """生成分析报告"""
    lines = [
        "# ESG数据智能提取与分析 — 分析报告",
        "",
        "## 一、数据概览",
        f"- 覆盖公司: {df['公司'].nunique()}家",
        f"- 覆盖行业: {df['行业'].nunique()}个",
        f"- 数据年份: {', '.join(sorted(str(y) for y in df['年份'].unique()))}",
        f"- 定量指标数据点: {len(df)}个",
        f"- 指标定义: 52个 (31定量 + 21定性)",
        "",
        "## 二、ESG综合排名 TOP20",
        "",
        "| 排名 | 公司 | 行业 | E得分 | S得分 | G得分 | ESG综合 |",
        "|------|------|------|-------|-------|-------|---------|",
    ]
    for _, row in scores.head(20).iterrows():
        lines.append(
            f"| {int(row['排名'])} | {row['公司']} | {row['行业']} | "
            f"{row['E_得分']:.3f} | {row['S_得分']:.3f} | {row['G_得分']:.3f} | "
            f"{row['ESG综合']:.3f} |"
        )

    lines += [
        "",
        "## 三、行业对比",
        "",
        "| 行业 | 公司数 | 平均碳排放(吨) | 平均可再生(%) | 平均女性员工(%) | 平均研发占比(%) |",
        "|------|--------|---------------|-------------|---------------|---------------|",
    ]
    for _, row in industries.iterrows():
        lines.append(
            f"| {row['行业']} | {int(row['公司数'])} | "
            f"{row['平均碳排放(吨)']:,.0f}" if row['平均碳排放(吨)'] else "|  | "
            f"{row['平均可再生比例(%)']:.1f}" if row['平均可再生比例(%)'] else " | "
            f"{row['平均女性员工(%)']:.1f}" if row['平均女性员工(%)'] else " | "
            f"{row['平均研发占比(%)']:.2f}" if row['平均研发占比(%)'] else " | "
        )

    lines += [
        "",
        "## 四、关键洞察",
        "",
    ]
    for ins in insights:
        lines.append(f"- **[{ins['类别']}]** {ins['洞察']}")

    lines += [
        "",
        "## 五、数据质量",
        f"- 平均质量分: {df.groupby('公司')['质量分'].mean().mean():.3f}",
        f"- 平均覆盖度: {df.groupby('公司')['覆盖度'].mean().mean():.1f}%",
    ]

    return "\n".join(lines)


if __name__ == "__main__":
    run_full_analysis()
