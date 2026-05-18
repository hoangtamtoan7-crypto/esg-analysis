"""ESG数据适配层 — 封装现有数据加载和分析函数，为Agent工具提供统一查询接口"""

import json
from pathlib import Path
from collections import defaultdict

import pandas as pd

from src.extractor.indicators import ALL_INDICATORS, INDICATORS_BY_DIMENSION, ESGIndicator

BASE_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"

# 行业分类映射
INDUSTRY_MAP = [
    ("银行", "金融"), ("保险", "金融"), ("证券", "金融"), ("太保", "金融"),
    ("财富", "金融"), ("华泰", "金融"), ("同花顺", "金融"),
    ("茅台", "食品饮料"), ("五粮液", "食品饮料"), ("老窖", "食品饮料"),
    ("汾酒", "食品饮料"), ("洋河", "食品饮料"), ("古井", "食品饮料"),
    ("伊利", "食品饮料"), ("海天", "食品饮料"), ("双汇", "食品饮料"), ("啤酒", "食品饮料"),
    ("医药", "医药"), ("制药", "医药"), ("医疗", "医药"), ("药明", "医药"),
    ("爱尔", "医药"), ("白药", "医药"), ("片仔", "医药"),
    ("泰格", "医药"), ("康龙", "医药"), ("智飞", "医药"),
    ("石油", "能源"), ("石化", "能源"), ("煤炭", "能源"), ("神华", "能源"),
    ("电力", "能源"), ("核电", "能源"), ("煤业", "能源"), ("兖矿", "能源"), ("华能", "能源"),
    ("科技", "科技"), ("海康", "科技"), ("大华", "科技"), ("讯飞", "科技"),
    ("金山", "科技"), ("京东方", "科技"), ("紫光", "科技"), ("立讯", "科技"),
    ("蓝思", "科技"), ("圣邦", "科技"), ("卓胜", "科技"), ("兆易", "科技"),
    ("中微", "科技"), ("北方华创", "科技"), ("三环", "科技"),
    ("汇川", "科技"), ("国电南瑞", "科技"), ("TCL", "科技"), ("中兴", "科技"),
    ("传音", "科技"), ("中芯", "科技"),
    ("比亚迪", "汽车"), ("上汽", "汽车"), ("长安汽车", "汽车"),
    ("广汽", "汽车"), ("福耀", "汽车"),
    ("美的", "制造业"), ("格力", "制造业"), ("海尔", "制造业"),
    ("重工", "制造业"), ("三一", "制造业"), ("潍柴", "制造业"),
    ("船舶", "制造业"), ("航发", "制造业"),
    ("钢铁", "材料"), ("钢股份", "材料"), ("特钢", "材料"), ("水泥", "材料"),
    ("化学", "材料"), ("万华", "材料"), ("建材", "材料"), ("雨虹", "材料"),
    ("万科", "房地产"), ("招商蛇口", "房地产"), ("保利", "房地产"), ("中国建筑", "建筑"),
    ("航空", "交通运输"), ("国航", "交通运输"), ("东航", "交通运输"),
    ("南航", "交通运输"), ("机场", "交通运输"), ("铁路", "交通运输"),
    ("顺丰", "交通运输"), ("远洋", "交通运输"), ("中远海控", "交通运输"),
    ("隆基", "新能源"), ("阳光电源", "新能源"), ("通威", "新能源"),
    ("中环", "新能源"), ("赣锋", "新能源"), ("宁德时代", "新能源"),
    ("牧原", "农业"), ("温氏", "农业"), ("海大", "农业"),
    ("分众", "传媒"), ("芒果", "传媒"),
    ("电信", "通信"), ("联通", "通信"), ("移动", "通信"),
]


def _classify_industry(name: str) -> str:
    for kw, ind in INDUSTRY_MAP:
        if kw in name:
            return ind
    return "其他"


def _round_floats(obj, decimals=3):
    """递归地将浮点数四舍五入，减少token消耗"""
    if isinstance(obj, dict):
        return {k: _round_floats(v, decimals) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_round_floats(v, decimals) for v in obj]
    elif isinstance(obj, float):
        return round(obj, decimals)
    return obj


class ESGDataAdapter:
    """ESG数据适配器 — 预加载所有数据，暴露查询方法"""

    def __init__(self):
        self.indicator_map = {i.id: i for i in ALL_INDICATORS}
        self._load_raw_results()
        self._build_df()
        self._compute_scores()
        self._build_industry_analysis()
        self._build_company_index()
        self._build_insights()

    def _load_raw_results(self):
        """加载原始JSON提取结果"""
        self.raw_results = []
        if OUTPUT_DIR.exists():
            for f in sorted(OUTPUT_DIR.glob("*_result.json")):
                with open(f, "r", encoding="utf-8") as fp:
                    self.raw_results.append(json.load(fp))

    def _build_df(self):
        """构建扁平化DataFrame"""
        rows = []
        for r in self.raw_results:
            company = r.get("company_name", "")
            year = r.get("report_year", "")
            validation = r.get("validation", {})
            completeness = r.get("completeness", {})
            quality = validation.get("overall_quality_score", 0)
            coverage = completeness.get("completeness", 0)

            if coverage == 0:
                continue

            industry = _classify_industry(company)

            for item in r.get("quantitative_indicators", []):
                val = item.get("value")
                if val is None or not isinstance(val, (int, float)):
                    continue
                rows.append({
                    "公司": company,
                    "行业": industry,
                    "年份": year,
                    "指标ID": item.get("id"),
                    "指标名称": item.get("name", ""),
                    "数值": val,
                    "单位": item.get("unit", ""),
                    "置信度": item.get("confidence", ""),
                    "质量分": quality,
                    "覆盖度": coverage,
                })

        self.df = pd.DataFrame(rows)

    def _compute_scores(self):
        """计算ESG综合评分"""
        if self.df.empty:
            self.scores = pd.DataFrame()
            return

        companies = []
        for name, group in self.df.groupby("公司"):
            scores_row = {"公司": name, "行业": group["行业"].iloc[0]}

            # E维度
            e_items = group[group["指标ID"].str.startswith("E_")]
            e_score, e_count = 0, 0
            for ind_id in ["E_Q01", "E_Q06", "E_Q10"]:
                vals = e_items[e_items["指标ID"] == ind_id]["数值"]
                if len(vals) > 0 and vals.iloc[0] > 0:
                    e_score += 1 if ind_id != "E_Q06" else min(vals.iloc[0] / 100, 1)
                    e_count += 1
            scores_row["E_得分"] = round(e_score / max(e_count, 1), 3)

            # S维度
            s_items = group[group["指标ID"].str.startswith("S_")]
            s_score, s_count = 0, 0
            for ind_id in ["S_Q05", "S_Q08", "S_Q02"]:
                vals = s_items[s_items["指标ID"] == ind_id]["数值"]
                if len(vals) > 0:
                    if ind_id == "S_Q05":
                        s_score += min(vals.iloc[0] / 100, 1)
                    elif ind_id == "S_Q08":
                        s_score += min(vals.iloc[0] / 20, 1)
                    elif ind_id == "S_Q02":
                        s_score += min(vals.iloc[0] / 50, 1)
                    s_count += 1
            scores_row["S_得分"] = round(s_score / max(s_count, 1), 3)

            # G维度
            g_items = group[group["指标ID"].str.startswith("G_")]
            g_score, g_count = 0, 0
            for ind_id in ["G_Q02", "G_Q04"]:
                vals = g_items[g_items["指标ID"] == ind_id]["数值"]
                if len(vals) > 0:
                    g_score += min(vals.iloc[0] / (50 if ind_id == "G_Q02" else 12), 1)
                    g_count += 1
            scores_row["G_得分"] = round(g_score / max(g_count, 1), 3)
            scores_row["ESG综合"] = round((scores_row["E_得分"] + scores_row["S_得分"] + scores_row["G_得分"]) / 3, 3)
            companies.append(scores_row)

        result = pd.DataFrame(companies).sort_values("ESG综合", ascending=False).reset_index(drop=True)
        result["排名"] = range(1, len(result) + 1)
        self.scores = result[["排名", "公司", "行业", "E_得分", "S_得分", "G_得分", "ESG综合"]]

    def _build_industry_analysis(self):
        """按行业汇总分析"""
        if self.df.empty:
            self.industries = pd.DataFrame()
            return

        industries = []
        for name, group in self.df.groupby("行业"):
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
        self.industries = pd.DataFrame(industries).sort_values("公司数", ascending=False)

    def _build_company_index(self):
        """构建公司名→详细信息的快速索引"""
        self.company_index = {}
        for r in self.raw_results:
            name = r.get("company_name", "")
            year = r.get("report_year", "")
            validation = r.get("validation", {})
            completeness = r.get("completeness", {})
            coverage = completeness.get("completeness", 0)
            if coverage == 0:
                continue
            self.company_index[name] = {
                "name": name,
                "year": year,
                "industry": _classify_industry(name),
                "quality": validation.get("overall_quality_score", 0),
                "coverage": coverage,
                "quantitative": r.get("quantitative_indicators", []),
                "qualitative": r.get("qualitative_indicators", []),
            }

        self.companies = sorted(self.company_index.keys())
        self.industries_list = sorted(set(
            info["industry"] for info in self.company_index.values()
        ))

    def _build_insights(self):
        """生成关键数据洞察"""
        self.insights = []
        if self.df.empty:
            return

        ghg = self.df[self.df["指标ID"] == "E_Q01"].dropna(subset=["数值"])
        if len(ghg) > 0:
            top = ghg.nlargest(3, "数值")
            self.insights.append({
                "类别": "环境",
                "洞察": f"碳排放最高: {', '.join(f'{r.公司}({r.数值:,.0f}吨)' for _, r in top.iterrows())}"
            })

        renewable = self.df[self.df["指标ID"] == "E_Q06"].dropna(subset=["数值"])
        if len(renewable) > 0:
            top = renewable.nlargest(3, "数值")
            self.insights.append({
                "类别": "环境",
                "洞察": f"可再生能源比例最高: {', '.join(f'{r.公司}({r.数值:.1f}%)' for _, r in top.iterrows())}"
            })

        rd = self.df[self.df["指标ID"] == "S_Q08"].dropna(subset=["数值"])
        if len(rd) > 0:
            top = rd.nlargest(3, "数值")
            self.insights.append({
                "类别": "社会",
                "洞察": f"研发投入占比最高: {', '.join(f'{r.公司}({r.数值:.2f}%)' for _, r in top.iterrows())}"
            })

        female = self.df[self.df["指标ID"] == "S_Q02"].dropna(subset=["数值"])
        if len(female) > 0:
            top = female.nlargest(3, "数值")
            self.insights.append({
                "类别": "社会",
                "洞察": f"女性员工比例最高: {', '.join(f'{r.公司}({r.数值:.1f}%)' for _, r in top.iterrows())}"
            })

        quality_scores = self.df.groupby("公司")["质量分"].mean()
        self.insights.append({
            "类别": "数据质量",
            "洞察": f"平均质量分: {quality_scores.mean():.3f}, 最高: {quality_scores.max():.3f}"
        })

        self.insights.append({
            "类别": "总体",
            "洞察": f"覆盖{self.df['行业'].nunique()}个行业、{self.df['公司'].nunique()}家A股上市公司"
        })

    # ====== 查询接口 ======

    def get_companies(self, industry: str = None) -> list:
        """列出公司名单，支持行业筛选"""
        results = []
        for name, info in self.company_index.items():
            if industry and info["industry"] != industry:
                continue
            results.append({
                "公司": name,
                "行业": info["industry"],
                "年份": info["year"],
                "质量分": round(info["quality"], 3),
            })
        return results

    def get_indicators(self, dimension: str = None, keyword: str = None) -> list:
        """查询指标体系，支持按维度和关键词筛选"""
        results = []
        for ind in ALL_INDICATORS:
            if dimension and ind.dimension != dimension:
                continue
            if keyword:
                text = ind.name + " ".join(ind.keywords)
                if keyword.lower() not in text.lower():
                    continue
            results.append({
                "id": ind.id,
                "name": ind.name,
                "dimension": ind.dimension,
                "type": ind.indicator_type,
                "unit": ind.unit,
                "description": ind.description,
            })
        return results

    def get_company_data(self, company_name: str, dimension: str = None) -> dict:
        """获取指定公司的ESG指标数据"""
        info = self.company_index.get(company_name)
        if not info:
            return {"error": f"未找到公司'{company_name}'", "suggestions": self._fuzzy_match_company(company_name)}

        score_row = self.scores[self.scores["公司"] == company_name]
        result = {
            "公司": company_name,
            "行业": info["industry"],
            "年份": info["year"],
            "质量分": round(info["quality"], 3),
            "覆盖度": info["coverage"],
        }
        if not score_row.empty:
            result["ESG得分"] = {
                "排名": int(score_row["排名"].iloc[0]),
                "E_得分": score_row["E_得分"].iloc[0],
                "S_得分": score_row["S_得分"].iloc[0],
                "G_得分": score_row["G_得分"].iloc[0],
                "ESG综合": score_row["ESG综合"].iloc[0],
            }

        quantitative = []
        for item in info["quantitative"]:
            ind_id = item.get("id", "")
            if dimension and not ind_id.startswith(dimension):
                continue
            ind_def = self.indicator_map.get(ind_id)
            quantitative.append({
                "指标ID": ind_id,
                "指标名称": ind_def.name if ind_def else item.get("name", ""),
                "数值": item.get("value"),
                "单位": item.get("unit", ""),
                "置信度": item.get("confidence", ""),
            })

        qualitative = []
        for item in info["qualitative"]:
            ind_id = item.get("id", "")
            if dimension and not ind_id.startswith(dimension):
                continue
            ind_def = self.indicator_map.get(ind_id)
            qualitative.append({
                "指标ID": ind_id,
                "指标名称": ind_def.name if ind_def else item.get("name", ""),
                "状态": item.get("status", ""),
                "摘要": (item.get("summary") or "")[:200],
                "置信度": item.get("confidence", ""),
            })

        result["定量指标"] = quantitative
        result["定性指标"] = qualitative
        return result

    def get_esg_scores(self, top_n: int = 10, company_names: list = None) -> list:
        """获取ESG评分排名"""
        if company_names:
            filtered = self.scores[self.scores["公司"].isin(company_names)]
            return _round_floats(filtered.to_dict(orient="records"))
        return _round_floats(self.scores.head(top_n).to_dict(orient="records"))

    def compare_companies(self, company_names: list, indicator_keywords: list = None) -> dict:
        """对比多家公司在特定指标上的数值"""
        # 解析指标
        resolved = []
        if indicator_keywords:
            for kw in indicator_keywords:
                matches = self._resolve_indicators(kw)
                resolved.extend(matches[:3])  # 每个关键词最多3个匹配
        else:
            # 默认对比关键指标
            default_ids = ["E_Q01", "E_Q06", "S_Q02", "S_Q08", "G_Q02", "G_Q04"]
            resolved = [{"id": iid, "name": self.indicator_map[iid].name} for iid in default_ids if iid in self.indicator_map]
        resolved = list({r["id"]: r for r in resolved}.values())  # 去重

        # 查数据
        comparisons = []
        for company in company_names:
            info = self.company_index.get(company)
            if not info:
                comparisons.append({"公司": company, "error": "未找到"})
                continue

            row = {"公司": company, "行业": info["industry"], "年份": info["year"]}
            qt_by_id = {item.get("id"): item for item in info["quantitative"]}
            for r in resolved:
                item = qt_by_id.get(r["id"])
                row[r["name"]] = item.get("value") if item else None
            comparisons.append(row)

        return {
            "指标": resolved,
            "对比数据": comparisons,
        }

    def get_industry_analysis(self, industry: str = None) -> list:
        """获取行业对比分析"""
        df = self.industries
        if industry:
            df = df[df["行业"] == industry]
        return _round_floats(df.to_dict(orient="records"))

    def get_trend(self, company_name: str, indicator_keyword: str) -> dict:
        """查询跨年份趋势（目前主要是单年份，返回该指标历史数据）"""
        info = self.company_index.get(company_name)
        if not info:
            return {"error": f"未找到公司'{company_name}'", "suggestions": self._fuzzy_match_company(company_name)}

        resolved = self._resolve_indicators(indicator_keyword)[:3]
        if not resolved:
            return {"error": f"未找到与'{indicator_keyword}'相关的指标", "data": []}

        trend_data = []
        for r in resolved:
            ind_id = r["id"]
            # 从所有报告中查找该公司的该指标
            values = []
            for raw in self.raw_results:
                if raw.get("company_name") == company_name:
                    year = raw.get("report_year", "")
                    for item in raw.get("quantitative_indicators", []):
                        if item.get("id") == ind_id and item.get("value") is not None:
                            values.append({
                                "年份": year,
                                "指标": r["name"],
                                "数值": item["value"],
                                "单位": item.get("unit", ""),
                            })
            if values:
                trend_data.extend(values)
            else:
                trend_data.append({
                    "指标": r["name"],
                    "数据": None,
                    "说明": "该指标暂无数据或数据为空"
                })

        return {"公司": company_name, "趋势数据": trend_data or []}

    def get_data_overview(self) -> dict:
        """数据整体概览"""
        if self.df.empty:
            return {"error": "暂无数据", "公司数": 0, "报告数": len(self.raw_results)}

        return {
            "公司数": len(self.companies),
            "报告数": len(self.raw_results),
            "行业数": len(self.industries_list),
            "行业": self.industries_list,
            "数据年份": sorted(set(str(y) for y in self.df["年份"].unique())) if "年份" in self.df.columns else [],
            "定量指标数": len([i for i in ALL_INDICATORS if i.indicator_type == "quantitative"]),
            "定性指标数": len([i for i in ALL_INDICATORS if i.indicator_type == "qualitative"]),
            "平均质量分": round(self.df.groupby("公司")["质量分"].mean().mean(), 3),
            "平均覆盖度": round(self.df.groupby("公司")["覆盖度"].mean().mean(), 1),
        }

    def get_top_by_indicator(self, indicator_keyword: str, top_n: int = 10) -> list:
        """按某个指标数值排名"""
        resolved = self._resolve_indicators(indicator_keyword, quantitative_only=True)
        if not resolved:
            return []

        ind_id = resolved[0]["id"]
        subset = self.df[self.df["指标ID"] == ind_id].dropna(subset=["数值"])
        top = subset.nlargest(min(top_n, len(subset)), "数值")
        return _round_floats(top[["公司", "行业", "年份", "指标名称", "数值", "单位", "置信度"]].to_dict(orient="records"))

    def search_companies_by_indicator(self, indicator_keyword: str, top_n: int = 10) -> list:
        """搜索在某个指标上有数据的公司"""
        resolved = self._resolve_indicators(indicator_keyword)
        if not resolved:
            return []

        companies_with_data = set()
        ind_ids = {r["id"] for r in resolved}
        for info in self.company_index.values():
            for item in info["quantitative"]:
                if item.get("id") in ind_ids and item.get("value") is not None:
                    companies_with_data.add(info["name"])
                    break
            for item in info["qualitative"]:
                if item.get("id") in ind_ids and item.get("status") in ("yes", "partial"):
                    companies_with_data.add(info["name"])
                    break

        return sorted(companies_with_data)[:top_n]

    # ====== 内部辅助 ======

    def _resolve_indicators(self, keyword: str, quantitative_only: bool = False) -> list:
        """根据关键词模糊匹配指标"""
        matches = []
        keyword_lower = keyword.lower()
        for ind in ALL_INDICATORS:
            if quantitative_only and ind.indicator_type != "quantitative":
                continue
            text = ind.name + " " + " ".join(ind.keywords) + " " + ind.description
            if keyword_lower in text.lower():
                matches.append({"id": ind.id, "name": ind.name, "unit": ind.unit})
        return sorted(matches, key=lambda x: len(x["name"]))

    def _fuzzy_match_company(self, name: str, limit: int = 5) -> list:
        """模糊匹配公司名"""
        name_lower = name.lower()
        matches = []
        for c in self.companies:
            if name_lower in c.lower():
                matches.append((c, 1))
            else:
                # 简单字符重叠得分
                overlap = len(set(name_lower) & set(c.lower()))
                if overlap > 0:
                    matches.append((c, overlap / max(len(name_lower), len(c))))
        matches.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in matches[:limit]]
