"""ESG指标体系定义

定义50+个关键ESG指标，覆盖环境(E)、社会(S)、治理(G)三个维度。
每个指标包含：名称、类型(quantitative/qualitative)、单位(如适用)、搜索关键词。
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ESGIndicator:
    id: str                         # 唯一标识
    name: str                       # 指标中文名称
    name_en: str                    # 指标英文名称
    dimension: str                  # E / S / G
    indicator_type: str             # quantitative / qualitative
    unit: Optional[str] = None      # 定量指标的单位
    keywords: List[str] = field(default_factory=list)  # 搜索关键词
    description: str = ""           # 补充说明


# ==================== E - 环境维度 ====================
ENVIRONMENTAL_INDICATORS = [
    # ---- 定量指标 ----
    ESGIndicator(
        id="E_Q01", name="温室气体排放总量", name_en="Total GHG Emissions",
        dimension="E", indicator_type="quantitative", unit="吨二氧化碳当量(tCO2e)",
        keywords=["温室气体", "碳排放", "GHG", "CO2", "二氧化碳", "排放总量"],
        description="范围1+范围2温室气体排放总量"
    ),
    ESGIndicator(
        id="E_Q02", name="范围1排放", name_en="Scope 1 Emissions",
        dimension="E", indicator_type="quantitative", unit="吨二氧化碳当量(tCO2e)",
        keywords=["范围一", "范围1", "Scope 1", "直接排放"],
        description="企业直接温室气体排放"
    ),
    ESGIndicator(
        id="E_Q03", name="范围2排放", name_en="Scope 2 Emissions",
        dimension="E", indicator_type="quantitative", unit="吨二氧化碳当量(tCO2e)",
        keywords=["范围二", "范围2", "Scope 2", "间接排放", "能源间接"],
        description="能源间接温室气体排放"
    ),
    ESGIndicator(
        id="E_Q04", name="温室气体排放强度", name_en="GHG Emission Intensity",
        dimension="E", indicator_type="quantitative", unit="吨二氧化碳当量/万元营收",
        keywords=["排放强度", "碳强度", "单位营收排放"],
        description="每单位营收的温室气体排放量"
    ),
    ESGIndicator(
        id="E_Q05", name="综合能源消耗", name_en="Total Energy Consumption",
        dimension="E", indicator_type="quantitative", unit="兆瓦时(MWh)",
        keywords=["能源消耗", "能耗", "用电量", "能源使用", "综合能耗"],
        description="企业所有能源消耗总量"
    ),
    ESGIndicator(
        id="E_Q06", name="可再生能源使用比例", name_en="Renewable Energy Ratio",
        dimension="E", indicator_type="quantitative", unit="%",
        keywords=["可再生能源", "绿电", "清洁能源", "光伏", "风电", "可再生能源占比"],
        description="可再生能源占总能源消耗的比例"
    ),
    ESGIndicator(
        id="E_Q07", name="总用水量", name_en="Total Water Consumption",
        dimension="E", indicator_type="quantitative", unit="吨",
        keywords=["用水量", "水资源", "耗水", "取水量", "用水"],
        description="企业年度总用水量"
    ),
    ESGIndicator(
        id="E_Q08", name="废水排放量", name_en="Wastewater Discharge",
        dimension="E", indicator_type="quantitative", unit="吨",
        keywords=["废水", "污水", "排水", "废水排放"],
        description="年度废水排放总量"
    ),
    ESGIndicator(
        id="E_Q09", name="废弃物产生总量", name_en="Total Waste Generated",
        dimension="E", indicator_type="quantitative", unit="吨",
        keywords=["废弃物", "固废", "垃圾", "废弃物产生", "废物"],
        description="年度废弃物产生总量"
    ),
    ESGIndicator(
        id="E_Q10", name="环保投入金额", name_en="Environmental Investment",
        dimension="E", indicator_type="quantitative", unit="万元",
        keywords=["环保投入", "环保投资", "环保支出", "环境治理投入", "环保资金"],
        description="年度环境保护总投入"
    ),
    ESGIndicator(
        id="E_Q11", name="氮氧化物排放", name_en="NOx Emissions",
        dimension="E", indicator_type="quantitative", unit="吨",
        keywords=["NOx", "氮氧化物", "NOX"],
        description="氮氧化物排放量"
    ),
    ESGIndicator(
        id="E_Q12", name="硫氧化物排放", name_en="SOx Emissions",
        dimension="E", indicator_type="quantitative", unit="吨",
        keywords=["SOx", "SO2", "硫氧化物", "二氧化硫"],
        description="硫氧化物排放量"
    ),
    ESGIndicator(
        id="E_Q13", name="颗粒物排放", name_en="Particulate Matter Emissions",
        dimension="E", indicator_type="quantitative", unit="吨",
        keywords=["颗粒物", "PM", "粉尘", "烟尘"],
        description="颗粒物排放总量"
    ),

    # ---- 定性指标 ----
    ESGIndicator(
        id="E_L01", name="气候变化应对策略", name_en="Climate Change Strategy",
        dimension="E", indicator_type="qualitative",
        keywords=["气候变化", "碳达峰", "碳中和", "低碳", "气候目标", "减排目标"],
        description="公司是否制定气候变化应对策略或碳中和路线图"
    ),
    ESGIndicator(
        id="E_L02", name="环境管理体系", name_en="Environmental Management System",
        dimension="E", indicator_type="qualitative",
        keywords=["环境管理", "ISO14001", "环境体系", "EMS"],
        description="是否建立并通过环境管理体系认证（如ISO14001）"
    ),
    ESGIndicator(
        id="E_L03", name="绿色产品与服务", name_en="Green Products & Services",
        dimension="E", indicator_type="qualitative",
        keywords=["绿色产品", "绿色服务", "节能产品", "环保产品", "绿色设计"],
        description="是否提供或研发绿色环保产品与服务"
    ),
    ESGIndicator(
        id="E_L04", name="生物多样性保护", name_en="Biodiversity Conservation",
        dimension="E", indicator_type="qualitative",
        keywords=["生物多样性", "生态保护", "栖息地", "物种"],
        description="是否有生物多样性保护政策或行动"
    ),
    ESGIndicator(
        id="E_L05", name="循环经济实践", name_en="Circular Economy Practices",
        dimension="E", indicator_type="qualitative",
        keywords=["循环经济", "资源循环", "废物利用", "回收利用", "循环利用"],
        description="是否有循环经济或资源循环利用相关实践"
    ),
]

# ==================== S - 社会维度 ====================
SOCIAL_INDICATORS = [
    # ---- 定量指标 ----
    ESGIndicator(
        id="S_Q01", name="员工总数", name_en="Total Employees",
        dimension="S", indicator_type="quantitative", unit="人",
        keywords=["员工总数", "员工人数", "在职员工", "雇员"],
        description="报告期末在职员工总数"
    ),
    ESGIndicator(
        id="S_Q02", name="女性员工比例", name_en="Female Employee Ratio",
        dimension="S", indicator_type="quantitative", unit="%",
        keywords=["女性员工", "女员工", "女性占比", "女职工"],
        description="女性员工占员工总数的比例"
    ),
    ESGIndicator(
        id="S_Q03", name="女性高管比例", name_en="Female Senior Management Ratio",
        dimension="S", indicator_type="quantitative", unit="%",
        keywords=["女性高管", "女性管理层", "女性管理者", "女性领导"],
        description="女性在高级管理层的占比"
    ),
    ESGIndicator(
        id="S_Q04", name="员工培训投入", name_en="Employee Training Investment",
        dimension="S", indicator_type="quantitative", unit="万元",
        keywords=["培训投入", "培训支出", "培训经费", "培训费用"],
        description="年度员工培训总投入金额"
    ),
    ESGIndicator(
        id="S_Q05", name="员工培训时长", name_en="Average Training Hours",
        dimension="S", indicator_type="quantitative", unit="小时/人",
        keywords=["培训时长", "人均培训", "培训小时", "培训时间"],
        description="员工人均年度培训时长"
    ),
    ESGIndicator(
        id="S_Q06", name="员工流失率", name_en="Employee Turnover Rate",
        dimension="S", indicator_type="quantitative", unit="%",
        keywords=["员工流失", "离职率", "流失率", "turnover"],
        description="年度员工主动离职率"
    ),
    ESGIndicator(
        id="S_Q07", name="研发投入金额", name_en="R&D Investment",
        dimension="S", indicator_type="quantitative", unit="万元",
        keywords=["研发投入", "研发支出", "R&D", "研究开发", "科研投入"],
        description="年度研发投入总额"
    ),
    ESGIndicator(
        id="S_Q08", name="研发投入占营收比例", name_en="R&D to Revenue Ratio",
        dimension="S", indicator_type="quantitative", unit="%",
        keywords=["研发占比", "研发强度", "研发/营收"],
        description="研发投入占营业收入的比例"
    ),
    ESGIndicator(
        id="S_Q09", name="安全生产投入", name_en="Safety Production Investment",
        dimension="S", indicator_type="quantitative", unit="万元",
        keywords=["安全投入", "安全生产", "安全经费", "安全支出"],
        description="年度安全生产投入总金额"
    ),
    ESGIndicator(
        id="S_Q10", name="工伤事故率", name_en="Work Injury Rate",
        dimension="S", indicator_type="quantitative", unit="‰",
        keywords=["工伤", "事故率", "工伤率", "安全事故", "千人负伤率"],
        description="每千名员工的工伤事故率"
    ),
    ESGIndicator(
        id="S_Q11", name="社会公益捐赠", name_en="Social Donations",
        dimension="S", indicator_type="quantitative", unit="万元",
        keywords=["捐赠", "公益", "慈善", "捐款", "扶贫"],
        description="年度社会公益捐赠总额"
    ),
    ESGIndicator(
        id="S_Q12", name="纳税总额", name_en="Total Tax Payment",
        dimension="S", indicator_type="quantitative", unit="万元",
        keywords=["纳税", "税收", "税务", "上缴税金"],
        description="年度纳税总额"
    ),

    # ---- 定性指标 ----
    ESGIndicator(
        id="S_L01", name="员工权益保护", name_en="Employee Rights Protection",
        dimension="S", indicator_type="qualitative",
        keywords=["员工权益", "劳动者权益", "劳动保障", "劳工权利", "员工福利"],
        description="是否有完善的员工权益保护政策"
    ),
    ESGIndicator(
        id="S_L02", name="职业健康安全管理", name_en="Occupational Health & Safety",
        dimension="S", indicator_type="qualitative",
        keywords=["职业健康", "安全管理体系", "ISO45001", "OHSAS"],
        description="是否建立职业健康安全管理体系"
    ),
    ESGIndicator(
        id="S_L03", name="供应链ESG管理", name_en="Supply Chain ESG Management",
        dimension="S", indicator_type="qualitative",
        keywords=["供应链管理", "供应商审核", "供应商评估", "负责任采购"],
        description="是否对供应链进行ESG评估和管理"
    ),
    ESGIndicator(
        id="S_L04", name="产品安全与质量", name_en="Product Safety & Quality",
        dimension="S", indicator_type="qualitative",
        keywords=["产品安全", "质量管理", "质量体系", "ISO9001", "产品召回"],
        description="是否有产品安全与质量管理体系"
    ),
    ESGIndicator(
        id="S_L05", name="数据安全与隐私保护", name_en="Data Security & Privacy",
        dimension="S", indicator_type="qualitative",
        keywords=["数据安全", "隐私保护", "信息安全", "个人信息", "网络安全"],
        description="是否有数据安全与隐私保护政策"
    ),
    ESGIndicator(
        id="S_L06", name="社区关系与参与", name_en="Community Engagement",
        dimension="S", indicator_type="qualitative",
        keywords=["社区", "社区参与", "社区发展", "社区关系", "乡村振兴"],
        description="是否有社区参与和发展计划"
    ),
    ESGIndicator(
        id="S_L07", name="员工多元化与包容", name_en="Diversity & Inclusion",
        dimension="S", indicator_type="qualitative",
        keywords=["多元化", "包容性", "平等", "反歧视", "DEI", "多元化政策"],
        description="是否有员工多元化与包容性政策"
    ),
]

# ==================== G - 治理维度 ====================
GOVERNANCE_INDICATORS = [
    # ---- 定量指标 ----
    ESGIndicator(
        id="G_Q01", name="董事会规模", name_en="Board Size",
        dimension="G", indicator_type="quantitative", unit="人",
        keywords=["董事会人数", "董事会规模", "董事人数"],
        description="董事会成员总人数"
    ),
    ESGIndicator(
        id="G_Q02", name="独立董事比例", name_en="Independent Director Ratio",
        dimension="G", indicator_type="quantitative", unit="%",
        keywords=["独立董事", "独董占比", "独立非执行董事"],
        description="独立董事占董事会总人数的比例"
    ),
    ESGIndicator(
        id="G_Q03", name="女性董事人数", name_en="Female Directors",
        dimension="G", indicator_type="quantitative", unit="人",
        keywords=["女性董事", "女董事", "女性董事会"],
        description="女性董事会成员数量"
    ),
    ESGIndicator(
        id="G_Q04", name="董事会会议次数", name_en="Board Meetings",
        dimension="G", indicator_type="quantitative", unit="次",
        keywords=["董事会会议", "董事会召开", "董事会议"],
        description="年度董事会会议召开次数"
    ),
    ESGIndicator(
        id="G_Q05", name="监事会规模", name_en="Supervisory Board Size",
        dimension="G", indicator_type="quantitative", unit="人",
        keywords=["监事会人数", "监事会规模", "监事人数"],
        description="监事会成员总人数"
    ),
    ESGIndicator(
        id="G_Q06", name="高管薪酬总额", name_en="Total Executive Compensation",
        dimension="G", indicator_type="quantitative", unit="万元",
        keywords=["高管薪酬", "高管报酬", "管理层薪酬"],
        description="年度高级管理人员薪酬总额"
    ),

    # ---- 定性指标 ----
    ESGIndicator(
        id="G_L01", name="ESG治理架构", name_en="ESG Governance Structure",
        dimension="G", indicator_type="qualitative",
        keywords=["ESG治理", "可持续发展委员会", "ESG委员会", "治理架构", "ESG管理"],
        description="是否设立ESG/可持续发展委员会或专门治理机构"
    ),
    ESGIndicator(
        id="G_L02", name="反腐败与廉洁建设", name_en="Anti-Corruption & Integrity",
        dimension="G", indicator_type="qualitative",
        keywords=["反腐败", "反贪污", "廉洁", "商业贿赂", "廉洁从业", "反腐"],
        description="是否有反腐败政策和廉洁建设机制"
    ),
    ESGIndicator(
        id="G_L03", name="商业道德与合规", name_en="Business Ethics & Compliance",
        dimension="G", indicator_type="qualitative",
        keywords=["商业道德", "合规管理", "道德准则", "行为准则", "合规体系"],
        description="是否有商业道德准则和合规管理体系"
    ),
    ESGIndicator(
        id="G_L04", name="风险管理体系", name_en="Risk Management Framework",
        dimension="G", indicator_type="qualitative",
        keywords=["风险管理", "风险管控", "风险体系", "内控", "内部控制"],
        description="是否建立全面风险管理体系"
    ),
    ESGIndicator(
        id="G_L05", name="投资者关系管理", name_en="Investor Relations",
        dimension="G", indicator_type="qualitative",
        keywords=["投资者关系", "IR", "股东沟通", "投资者沟通"],
        description="是否有完善的投资者关系管理制度"
    ),
    ESGIndicator(
        id="G_L06", name="利益相关方沟通", name_en="Stakeholder Engagement",
        dimension="G", indicator_type="qualitative",
        keywords=["利益相关方", "利益相关者", "stakeholder", "多方沟通"],
        description="是否开展利益相关方沟通与实质性议题分析"
    ),
    ESGIndicator(
        id="G_L07", name="信息披露质量", name_en="Information Disclosure Quality",
        dimension="G", indicator_type="qualitative",
        keywords=["信息披露", "透明度", "披露质量", "信息透明", "公开透明"],
        description="ESG信息披露是否参照GRI/TCFD/ISSB等国际标准"
    ),
    ESGIndicator(
        id="G_Q07", name="审计委员会会议次数", name_en="Audit Committee Meetings",
        dimension="G", indicator_type="quantitative", unit="次",
        keywords=["审计委员会", "审计委员会会议", "内审会议"],
        description="年度审计委员会会议召开次数"
    ),
    ESGIndicator(
        id="G_L08", name="税务透明度", name_en="Tax Transparency",
        dimension="G", indicator_type="qualitative",
        keywords=["税务透明", "税基侵蚀", "税收治理", "税务政策"],
        description="是否有税务透明度政策或税务治理框架"
    ),
]

# 汇总所有指标
ALL_INDICATORS = ENVIRONMENTAL_INDICATORS + SOCIAL_INDICATORS + GOVERNANCE_INDICATORS

# 按维度分组
INDICATORS_BY_DIMENSION = {
    "E": ENVIRONMENTAL_INDICATORS,
    "S": SOCIAL_INDICATORS,
    "G": GOVERNANCE_INDICATORS,
}

# 按类型分组
QUANTITATIVE_INDICATORS = [i for i in ALL_INDICATORS if i.indicator_type == "quantitative"]
QUALITATIVE_INDICATORS = [i for i in ALL_INDICATORS if i.indicator_type == "qualitative"]


def get_indicator_by_id(indicator_id: str) -> ESGIndicator:
    """根据ID获取指标定义"""
    for ind in ALL_INDICATORS:
        if ind.id == indicator_id:
            return ind
    raise ValueError(f"未找到指标: {indicator_id}")


def get_indicator_summary() -> dict:
    """获取指标统计摘要"""
    return {
        "total": len(ALL_INDICATORS),
        "E_quantitative": len([i for i in ENVIRONMENTAL_INDICATORS if i.indicator_type == "quantitative"]),
        "E_qualitative": len([i for i in ENVIRONMENTAL_INDICATORS if i.indicator_type == "qualitative"]),
        "S_quantitative": len([i for i in SOCIAL_INDICATORS if i.indicator_type == "quantitative"]),
        "S_qualitative": len([i for i in SOCIAL_INDICATORS if i.indicator_type == "qualitative"]),
        "G_quantitative": len([i for i in GOVERNANCE_INDICATORS if i.indicator_type == "quantitative"]),
        "G_qualitative": len([i for i in GOVERNANCE_INDICATORS if i.indicator_type == "qualitative"]),
    }


if __name__ == "__main__":
    summary = get_indicator_summary()
    print(f"ESG指标体系: 共{summary['total']}个指标")
    print(f"  环境(E): {summary['E_quantitative']}定量 + {summary['E_qualitative']}定性")
    print(f"  社会(S): {summary['S_quantitative']}定量 + {summary['S_qualitative']}定性")
    print(f"  治理(G): {summary['G_quantitative']}定量 + {summary['G_qualitative']}定性")
    print(f"\n定量指标: {len(QUANTITATIVE_INDICATORS)}个")
    for ind in QUANTITATIVE_INDICATORS:
        print(f"  [{ind.id}] {ind.name} ({ind.unit})")
    print(f"\n定性指标: {len(QUALITATIVE_INDICATORS)}个")
    for ind in QUALITATIVE_INDICATORS:
        print(f"  [{ind.id}] {ind.name}")
