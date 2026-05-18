"""ESG报告数据源配置

主要数据源：
1. 巨潮资讯网 (cninfo.com.cn) - A股官方信息披露平台
2. 港交所披露易 (hkexnews.hk) - 港股公告
3. 上交所 (sse.com.cn) - 沪市公告
4. 深交所 (szse.cn) - 深市公告
"""

from dataclasses import dataclass
from typing import List

@dataclass
class DataSource:
    name: str
    base_url: str
    search_url: str
    description: str


# 主要数据源 - 巨潮资讯网（最核心的数据来源）
CNINFO = DataSource(
    name="巨潮资讯网",
    base_url="http://www.cninfo.com.cn",
    search_url="http://www.cninfo.com.cn/new/fulltextSearch",
    description="A股官方信息披露平台，覆盖沪深两市所有上市公司公告"
)

# 搜索关键词（ESG报告的各种名称变体）
ESG_KEYWORDS = [
    "ESG报告",
    "可持续发展报告",
    "社会责任报告",
    "环境、社会及管治报告",
    "环境、社会与管治报告",
    "企业社会责任报告",
    "ESG Report",
    "Sustainability Report",
    "CSR报告",
]
