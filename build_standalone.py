"""构建自包含HTML — 零安装、浏览器直接打开、全部数据内嵌"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from src.agent.data_adapter import ESGDataAdapter
from src.extractor.indicators import ALL_INDICATORS

print("加载数据...")
adapter = ESGDataAdapter()

# ====== 准备所有数据 ======
data_pack = {
    "overview": adapter.get_data_overview(),
    "companies": adapter.get_companies(),
    "scores": adapter.scores.to_dict(orient="records") if not adapter.scores.empty else [],
    "industries": adapter.industries.to_dict(orient="records") if not adapter.industries.empty else [],
    "indicators": adapter.get_indicators(),
    "company_index": {},
}

# 为每家公司准备完整数据
for name, info in adapter.company_index.items():
    data_pack["company_index"][name] = {
        "name": name,
        "industry": info["industry"],
        "year": info["year"],
        "quality": info["quality"],
        "coverage": info["coverage"],
        "quantitative": [],
        "qualitative": [],
    }
    # ESG得分
    row = adapter.scores[adapter.scores["公司"] == name]
    if not row.empty:
        data_pack["company_index"][name]["esg_score"] = {
            "排名": int(row["排名"].iloc[0]),
            "E_得分": row["E_得分"].iloc[0],
            "S_得分": row["S_得分"].iloc[0],
            "G_得分": row["G_得分"].iloc[0],
            "ESG综合": row["ESG综合"].iloc[0],
        }
    for item in info["quantitative"]:
        data_pack["company_index"][name]["quantitative"].append({
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "value": item.get("value"),
            "unit": item.get("unit", ""),
            "confidence": item.get("confidence", ""),
        })
    for item in info["qualitative"]:
        data_pack["company_index"][name]["qualitative"].append({
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "status": item.get("status", ""),
            "summary": (item.get("summary") or "")[:200],
        })

# 转换为JSON（处理numpy类型）
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return round(float(obj), 3)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

data_json = json.dumps(data_pack, ensure_ascii=False, cls=NpEncoder)
print(f"数据大小: {len(data_json)//1024} KB")

# ====== HTML模板 ======
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESG数据智能提取与分析系统</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #f5f7fa; color: #333; }}
header {{ background: linear-gradient(135deg, #1a5276 0%, #2e86c1 100%); color: #fff; padding: 24px; text-align: center; }}
header h1 {{ font-size: 1.6em; margin-bottom: 6px; }}
header p {{ font-size: 0.9em; opacity: 0.85; }}
nav {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; background: #fff; padding: 10px; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
nav button {{ padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; font-size: 0.9em; white-space: nowrap; transition: .2s; }}
nav button:hover, nav button.active {{ background: #2e86c1; color: #fff; border-color: #2e86c1; }}
.container {{ max-width: 1300px; margin: 0 auto; padding: 16px; }}
section {{ display: none; }}
section.active {{ display: block; }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 12px; margin-bottom: 20px; }}
.kpi {{ background: #fff; padding: 18px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.06); }}
.kpi .num {{ font-size: 1.8em; font-weight: 700; color: #1a5276; }}
.kpi .label {{ font-size: .85em; color: #888; margin-top: 4px; }}
.card {{ background: #fff; padding: 16px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px; }}
.card h3 {{ margin-bottom: 10px; color: #444; font-size: 1.05em; }}
.chart-container {{ min-height: 300px; }}
.row2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
@media (max-width: 900px) {{ .row2 {{ grid-template-columns: 1fr; }} }}
table {{ width: 100%; border-collapse: collapse; font-size: .85em; }}
th {{ background: #1a5276; color: #fff; padding: 8px 10px; text-align: left; position: sticky; top: 0; }}
td {{ padding: 7px 10px; border-bottom: 1px solid #eee; }}
tr:hover {{ background: #f0f6ff; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: .8em; font-weight: 600; }}
.badge-green {{ background: #d4efdf; color: #1e8449; }}
.badge-blue {{ background: #d6eaf8; color: #2471a3; }}
.badge-red {{ background: #fadbd8; color: #c0392b; }}
.badge-gray {{ background: #e5e7e9; color: #717d7e; }}
input, select {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: .9em; width: 100%; }}
.input-row {{ display: flex; gap: 10px; margin-bottom: 12px; align-items: center; }}
.input-row input {{ flex: 1; }}
.input-row select {{ width: auto; min-width: 140px; }}
.search-results {{ margin-top: 8px; }}
.search-item {{ padding: 8px 12px; background: #f8f9fa; border-radius: 6px; margin-bottom: 6px; cursor: pointer; transition: .15s; }}
.search-item:hover {{ background: #e8f0fe; }}
.highlight {{ background: #ffeaa7; padding: 0 2px; border-radius: 2px; }}
.qual-status {{ font-weight: 600; }}
.qual-yes {{ color: #27ae60; }}
.qual-no {{ color: #e74c3c; }}
.qual-partial {{ color: #f39c12; }}
.dim-tabs {{ display: flex; gap: 6px; margin-bottom: 12px; }}
.dim-tab {{ padding: 6px 16px; border-radius: 16px; border: 1px solid #ddd; cursor: pointer; font-size: .85em; background: #fff; }}
.dim-tab.active {{ background: #2e86c1; color: #fff; border-color: #2e86c1; }}
footer {{ text-align: center; padding: 20px; color: #999; font-size: .8em; }}
</style>
</head>
<body>

<header>
  <h1>📊 ESG数据智能提取与分析系统</h1>
  <p>基于DeepSeek大模型 · A股上市公司ESG报告自动提取 · 数据要素大赛</p>
</header>

<nav>
  <button class="active" onclick="switchTab('overview')">📊 数据概览</button>
  <button onclick="switchTab('ranking')">🏆 ESG排名</button>
  <button onclick="switchTab('company')">🏢 公司查询</button>
  <button onclick="switchTab('compare')">📊 指标对比</button>
  <button onclick="switchTab('industry')">🏭 行业分析</button>
  <button onclick="switchTab('search')">🔍 智能检索</button>
</nav>

<div class="container">

<!-- ====== 数据概览 ====== -->
<section id="overview" class="active">
  <div class="kpi-grid" id="kpi-cards"></div>
  <div class="row2">
    <div class="card"><h3>行业ESG均值对比</h3><div class="chart-container" id="chart-industry-avg"></div></div>
    <div class="card"><h3>行业分布</h3><div class="chart-container" id="chart-industry-pie"></div></div>
  </div>
  <div class="card"><h3>公司数据总览</h3><div style="max-height:500px;overflow-y:auto"><table id="table-overview"><thead><tr><th>公司</th><th>行业</th><th>年份</th><th>质量分</th><th>覆盖度</th></tr></thead><tbody></tbody></table></div></div>
</section>

<!-- ====== ESG排名 ====== -->
<section id="ranking">
  <div class="card"><h3>ESG综合得分 TOP20</h3><div class="chart-container" id="chart-top20"></div></div>
  <div class="card"><h3>ESG评分明细表</h3><div style="max-height:600px;overflow-y:auto"><table id="table-scores"><thead><tr><th>排名</th><th>公司</th><th>行业</th><th>E得分</th><th>S得分</th><th>G得分</th><th>ESG综合</th></tr></thead><tbody></tbody></table></div></div>
  <div class="card"><h3>E/S/G维度雷达图 TOP6</h3><div class="chart-container" id="chart-radar"></div></div>
</section>

<!-- ====== 公司查询 ====== -->
<section id="company">
  <div class="input-row">
    <input type="text" id="company-search" placeholder="输入公司名称搜索，如'比亚迪'、'美的集团'..." oninput="searchCompany()">
  </div>
  <div id="company-list" class="search-results"></div>
  <div id="company-detail"></div>
</section>

<!-- ====== 指标对比 ====== -->
<section id="compare">
  <div class="input-row">
    <input type="text" id="compare-companies" placeholder="选择公司（用逗号分隔），如: 比亚迪,美的集团,格力电器">
  </div>
  <div class="input-row">
    <select id="compare-indicator" onchange="runCompare()">
      <option value="">选择对比指标...</option>
    </select>
  </div>
  <div class="card"><div class="chart-container" id="chart-compare"></div></div>
  <div class="card" id="compare-table-card" style="display:none"><h3>对比数据</h3><div style="max-height:400px;overflow-y:auto"><table id="table-compare"><thead></thead><tbody></tbody></table></div></div>
</section>

<!-- ====== 行业分析 ====== -->
<section id="industry">
  <div class="card"><h3>各行业ESG对比</h3><div style="max-height:500px;overflow-y:auto"><table id="table-industry"><thead><tr><th>行业</th><th>公司数</th><th>平均碳排放(吨)</th><th>平均可再生(%)</th><th>平均女性员工(%)</th><th>平均研发占比(%)</th></tr></thead><tbody></tbody></table></div></div>
  <div class="row2">
    <div class="card"><h3>行业碳排放对比</h3><div class="chart-container" id="chart-industry-ghg"></div></div>
    <div class="card"><h3>行业ESG均值排名</h3><div class="chart-container" id="chart-industry-esg"></div></div>
  </div>
</section>

<!-- ====== 智能检索 ====== -->
<section id="search">
  <div class="input-row">
    <input type="text" id="smart-search" placeholder="输入关键词检索，如'碳排放'、'女性员工'、'研发投入'..." oninput="smartSearch()">
    <select id="search-type" onchange="smartSearch()">
      <option value="all">全部</option>
      <option value="company">按公司</option>
      <option value="indicator">按指标</option>
    </select>
  </div>
  <div id="search-results" class="search-results"></div>
  <div class="card" id="search-chart-card" style="display:none"><h3 id="search-chart-title"></h3><div class="chart-container" id="chart-search"></div></div>
</section>

</div>

<footer>© ESG数据智能提取与分析系统 · 数据覆盖<span id="footer-count"></span>家A股上市公司 · 数据要素大赛</footer>

<script>
// ====== 内嵌数据 ======
const DATA = {data_json};

// ====== 全局状态 ======
let currentTab = 'overview';

// ====== 工具函数 ======
function fmt(n, digits) {{
  if (n === null || n === undefined || n === '') return '-';
  if (typeof n === 'number') return n.toLocaleString('zh-CN', {{maximumFractionDigits: digits||0}});
  return n;
}}

function statusIcon(s) {{
  const map = {{'yes':'✅','no':'❌','partial':'⚠️'}};
  return map[s] || '❓';
}}

function statusClass(s) {{
  const map = {{'yes':'qual-yes','no':'qual-no','partial':'qual-partial'}};
  return map[s] || '';
}}

function confBadge(c) {{
  const map = {{'high':'badge-green','medium':'badge-blue','low':'badge-red'}};
  return '<span class="badge '+(map[c]||'badge-gray')+'">'+(c||'?')+'</span>';
}}

// ====== Tab切换 ======
function switchTab(id) {{
  document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelector('nav button[onclick="switchTab(\\''+id+'\\')"]').classList.add('active');
  currentTab = id;
  if (id === 'overview') renderOverview();
  if (id === 'ranking') renderRanking();
  if (id === 'company') renderCompanySearch();
  if (id === 'compare') renderComparePage();
  if (id === 'industry') renderIndustryPage();
  if (id === 'search') smartSearch();
}}

// ====== 首页概览 ======
function renderOverview() {{
  const ov = DATA.overview;
  const scores = DATA.scores;

  // KPI
  const kpis = [
    {{num: ov['公司数']||0, label: '覆盖公司'}},
    {{num: ov['报告数']||0, label: 'ESG报告'}},
    {{num: ov['行业数']||0, label: '行业'}},
    {{num: ov['定量指标数']||0, label: '定量指标'}},
    {{num: ov['定性指标数']||0, label: '定性指标'}},
    {{num: (ov['平均质量分']||0).toFixed(3), label: '平均质量分'}},
  ];
  document.getElementById('kpi-cards').innerHTML = kpis.map(k =>
    '<div class="kpi"><div class="num">'+k.num+'</div><div class="label">'+k.label+'</div></div>'
  ).join('');

  // 行业ESG均值
  const indMap = {{}};
  scores.forEach(s => {{
    if (!indMap[s['行业']]) indMap[s['行业']] = [];
    indMap[s['行业']].push(s['ESG综合']);
  }});
  const indAvg = Object.entries(indMap).map(([k,v]) => ({{行业:k, ESG均值: v.reduce((a,b)=>a+b,0)/v.length}})).sort((a,b)=>b['ESG均值']-a['ESG均值']);
  Plotly.newPlot('chart-industry-avg', [{{
    x: indAvg.map(d=>d['行业']), y: indAvg.map(d=>d['ESG均值']),
    type: 'bar', marker: {{color: indAvg.map((_,i)=>'hsl('+(i*25)+',60%,50%)')}},
    text: indAvg.map(d=>d['ESG均值'].toFixed(3)), textposition: 'outside'
  }}], {{title:'行业ESG均值对比', showlegend:false, margin:{{t:40,b:80}}, height:350}});

  // 行业饼图
  const indCount = {{}};
  DATA.companies.forEach(c => {{ indCount[c['行业']] = (indCount[c['行业']]||0)+1; }});
  const pieData = Object.entries(indCount).sort((a,b)=>b[1]-a[1]);
  Plotly.newPlot('chart-industry-pie', [{{
    labels: pieData.map(d=>d[0]), values: pieData.map(d=>d[1]),
    type: 'pie', textinfo: 'label+value'
  }}], {{title:'行业分布', height:350}});

  // 表格
  const tbody = document.querySelector('#table-overview tbody');
  tbody.innerHTML = DATA.companies.slice(0,200).map(c =>
    '<tr><td>'+c['公司']+'</td><td>'+c['行业']+'</td><td>'+c['年份']+'</td><td>'+c['质量分']+'</td><td>'+(DATA.company_index[c['公司']]?DATA.company_index[c['公司']].coverage:'-')+'%</td></tr>'
  ).join('');

  document.getElementById('footer-count').textContent = ' '+(ov['公司数']||0)+' ';
}}

// ====== ESG排名 ======
function renderRanking() {{
  const scores = DATA.scores;
  const top20 = scores.slice(0,20);

  // 柱状图
  Plotly.newPlot('chart-top20', [{{
    y: top20.map(d=>d['公司']).reverse(),
    x: top20.map(d=>d['ESG综合']).reverse(),
    type: 'bar', orientation: 'h',
    marker: {{color: top20.map(d=>d['ESG综合']).reverse(), colorscale: 'Blues', showscale:true}},
    text: top20.map(d=>d['ESG综合'].toFixed(3)).reverse(), textposition: 'outside'
  }}], {{title:'ESG综合得分 TOP20', height:550, margin:{{l:100,r:40,t:40,b:40}}, yaxis:{{autorange:'reversed'}}}});

  // 雷达图
  const radarData = scores.slice(0,6).map(d => ({{
    type: 'scatterpolar',
    r: [d['E_得分'], d['S_得分'], d['G_得分'], d['E_得分']],
    theta: ['环境(E)','社会(S)','治理(G)','环境(E)'],
    name: d['公司'], fill: 'toself', opacity: 0.5
  }}));
  Plotly.newPlot('chart-radar', radarData, {{title:'TOP6 ESG维度雷达图', height:450, polar:{{radialaxis:{{range:[0,1.1]}}}}, margin:{{t:40,b:40}}}});

  // 评分表
  const tbody = document.querySelector('#table-scores tbody');
  tbody.innerHTML = scores.map(s =>
    '<tr><td>'+s['排名']+'</td><td><b>'+s['公司']+'</b></td><td>'+s['行业']+'</td><td>'+s['E_得分'].toFixed(3)+'</td><td>'+s['S_得分'].toFixed(3)+'</td><td>'+s['G_得分'].toFixed(3)+'</td><td><b>'+s['ESG综合'].toFixed(3)+'</b></td></tr>'
  ).join('');
}}

// ====== 公司查询 ======
function searchCompany() {{
  const q = document.getElementById('company-search').value.trim().toLowerCase();
  const list = document.getElementById('company-list');
  const detail = document.getElementById('company-detail');
  if (!q) {{ list.innerHTML = ''; detail.innerHTML = ''; return; }}

  const matches = DATA.companies.filter(c => c['公司'].toLowerCase().includes(q)).slice(0, 15);
  list.innerHTML = matches.map(c =>
    '<div class="search-item" onclick="showCompany(\''+c['公司']+'\')">'+
    '<b>'+c['公司']+'</b> <span style="color:#888">'+c['行业']+' · '+c['年份']+' · 质量分:'+c['质量分']+'</span>'+
    '</div>'
  ).join('');
  if (matches.length === 0) list.innerHTML = '<div style="color:#999;padding:12px">未找到匹配公司</div>';
}}

function showCompany(name) {{
  const info = DATA.company_index[name];
  if (!info) {{ document.getElementById('company-detail').innerHTML = '<div class="card">未找到该公司数据</div>'; return; }}

  const s = info.esg_score || {{}};
  let html = '<div class="card"><h3>'+name+' — '+info.industry+' · '+info.year+'年度</h3>';
  html += '<div class="kpi-grid">';
  html += '<div class="kpi"><div class="num">'+((info.quality||0)).toFixed(3)+'</div><div class="label">质量分</div></div>';
  html += '<div class="kpi"><div class="num">'+(info.coverage||0)+'%</div><div class="label">覆盖度</div></div>';
  html += '<div class="kpi"><div class="num">'+(s['ESG综合']||'-')+'</div><div class="label">ESG综合</div></div>';
  html += '<div class="kpi"><div class="num">#'+(s['排名']||'-')+'</div><div class="label">排名</div></div>';
  html += '</div>';

  // E/S/G得分柱状图
  if (s['E_得分'] !== undefined) {{
    html += '<div id="company-esg-chart" class="chart-container" style="height:300px"></div>';
    setTimeout(function() {{
      Plotly.newPlot('company-esg-chart', [{{
        x: ['环境(E)','社会(S)','治理(G)'],
        y: [s['E_得分'], s['S_得分'], s['G_得分']],
        type: 'bar', marker: {{color: ['#2ecc71','#3498db','#e74c3c']}},
        text: [s['E_得分'].toFixed(3), s['S_得分'].toFixed(3), s['G_得分'].toFixed(3)],
        textposition: 'outside'
      }}], {{title:name+' E/S/G维度得分', yaxis:{{range:[0,1.1]}}, height:300, margin:{{t:40}}}});
    }}, 100);
  }}

  html += '</div>';

  // 维度Tabs
  html += '<div class="dim-tabs">';
  html += '<button class="dim-tab active" onclick="switchDim(\''+name+'\',\'E\',this)">🌍 环境(E)</button>';
  html += '<button class="dim-tab" onclick="switchDim(\''+name+'\',\'S\',this)">👥 社会(S)</button>';
  html += '<button class="dim-tab" onclick="switchDim(\''+name+'\',\'G\',this)">🏛️ 治理(G)</button>';
  html += '</div>';
  html += '<div class="card" id="company-dim-detail"></div>';

  document.getElementById('company-detail').innerHTML = html;
  switchDim(name, 'E', document.querySelector('.dim-tab'));
}}

function switchDim(name, dim, btn) {{
  document.querySelectorAll('.dim-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const info = DATA.company_index[name];

  // 定量
  const qt = (info.quantitative||[]).filter(i => i.id && i.id.startsWith(dim));
  // 定性
  const ql = (info.qualitative||[]).filter(i => i.id && i.id.startsWith(dim));

  let html = '';
  if (qt.length > 0) {{
    html += '<h4>📏 定量指标</h4><table><tr><th>指标</th><th>数值</th><th>单位</th><th>置信度</th></tr>';
    qt.forEach(i => {{
      html += '<tr><td>'+i.name+'</td><td><b>'+fmt(i.value,2)+'</b></td><td>'+i.unit+'</td><td>'+confBadge(i.confidence)+'</td></tr>';
    }});
    html += '</table><br>';
  }}
  if (ql.length > 0) {{
    html += '<h4>📝 定性指标</h4><table><tr><th>指标</th><th>状态</th><th>摘要</th></tr>';
    ql.forEach(i => {{
      html += '<tr><td>'+i.name+'</td><td><span class="qual-status '+statusClass(i.status)+'">'+statusIcon(i.status)+' '+(i.status||'?')+'</span></td><td>'+(i.summary||'')+'</td></tr>';
    }});
    html += '</table>';
  }}
  if (qt.length === 0 && ql.length === 0) html = '<p style="color:#999">该维度暂无数据</p>';
  document.getElementById('company-dim-detail').innerHTML = html;
}}

// ====== 指标对比 ======
function renderComparePage() {{
  const sel = document.getElementById('compare-indicator');
  if (sel.options.length <= 1) {{
    const allNames = new Set();
    DATA.companies.forEach(c => {{
      const info = DATA.company_index[c['公司']];
      if (info) {{
        info.quantitative.forEach(i => {{ if (i.name && i.value!==null) allNames.add(i.name); }});
      }}
    }});
    sel.innerHTML = '<option value="">选择对比指标...</option>' + [...allNames].sort().map(n => '<option value="'+n+'">'+n+'</option>').join('');
  }}

  const companiesStr = document.getElementById('compare-companies').value.trim();
  if (companiesStr) runCompare();
}}

function runCompare() {{
  const companiesStr = document.getElementById('compare-companies').value.trim();
  const indName = document.getElementById('compare-indicator').value;
  if (!companiesStr || !indName) return;

  const companyNames = companiesStr.split(/[,，]+/).map(s => s.trim()).filter(Boolean);
  const rows = [];
  companyNames.forEach(name => {{
    const info = DATA.company_index[name];
    if (!info) {{ rows.push({{公司:name, 值:'未找到'}}); return; }}
    const item = info.quantitative.find(i => i.name === indName);
    rows.push({{公司:name, 行业:info.industry, 数值: item ? item.value : null, 单位: item ? item.unit : ''}});
  }});

  const valid = rows.filter(r => r['数值'] !== null && r['数值'] !== undefined);
  if (valid.length > 0) {{
    Plotly.newPlot('chart-compare', [{{
      x: valid.map(r=>r['公司']), y: valid.map(r=>r['数值']),
      type: 'bar', marker: {{color: valid.map((_,i)=>'hsl('+(i*60)+',60%,50%)')}},
      text: valid.map(r=>r['数值']!==null?r['数值'].toLocaleString():'-'), textposition: 'outside'
    }}], {{title: indName+' — 多公司对比', showlegend:false, height:400, margin:{{t:40,b:80}}}});
  }}

  const card = document.getElementById('compare-table-card');
  const thead = document.querySelector('#table-compare thead');
  const tbody = document.querySelector('#table-compare tbody');
  thead.innerHTML = '<tr><th>公司</th><th>行业</th><th>数值</th><th>单位</th></tr>';
  tbody.innerHTML = rows.map(r =>
    '<tr><td><b>'+r['公司']+'</b></td><td>'+r['行业']+'</td><td>'+(r['数值']!==null?fmt(r['数值'],2):'<span style="color:#999">无数据</span>')+'</td><td>'+r['单位']+'</td></tr>'
  ).join('');
  card.style.display = 'block';
}}

// ====== 行业分析 ======
function renderIndustryPage() {{
  const inds = DATA.industries;
  const tbody = document.querySelector('#table-industry tbody');
  tbody.innerHTML = inds.map(d =>
    '<tr><td><b>'+d['行业']+'</b></td><td>'+d['公司数']+'</td><td>'+fmt(d['平均碳排放(吨)'])+'</td><td>'+fmt(d['平均可再生比例(%)'],1)+'</td><td>'+fmt(d['平均女性员工(%)'],1)+'</td><td>'+fmt(d['平均研发占比(%)'],2)+'</td></tr>'
  ).join('');

  // 碳排放图
  const ghgData = inds.filter(d=>d['平均碳排放(吨)']!==null && d['平均碳排放(吨)']>0);
  if (ghgData.length>0) {{
    Plotly.newPlot('chart-industry-ghg', [{{
      x: ghgData.map(d=>d['行业']), y: ghgData.map(d=>d['平均碳排放(吨)']),
      type: 'bar', marker: {{color: ghgData.map((_,i)=>'hsl('+(i*25)+',60%,50%)')}}
    }}], {{title:'各行业平均碳排放(吨CO₂e)', showlegend:false, height:350, margin:{{t:40,b:80}}}});
  }}

  // ESG均值排名
  const indESG = {{}};
  DATA.scores.forEach(s => {{
    if (!indESG[s['行业']]) indESG[s['行业']] = [];
    indESG[s['行业']].push(s['ESG综合']);
  }});
  const esgData = Object.entries(indESG).map(([k,v])=>({{行业:k, ESG均值:v.reduce((a,b)=>a+b,0)/v.length}})).sort((a,b)=>b['ESG均值']-a['ESG均值']);
  Plotly.newPlot('chart-industry-esg', [{{
    x: esgData.map(d=>d['行业']), y: esgData.map(d=>d['ESG均值']),
    type: 'bar', marker: {{color: esgData.map((_,i)=>'hsl('+(i*25)+',60%,50%)')}},
    text: esgData.map(d=>d['ESG均值'].toFixed(3)), textposition: 'outside'
  }}], {{title:'各行业ESG均值排名', showlegend:false, height:350, margin:{{t:40,b:80}}}});
}}

// ====== 智能检索 ======
function smartSearch() {{
  const q = document.getElementById('smart-search').value.trim().toLowerCase();
  const type = document.getElementById('search-type').value;
  const container = document.getElementById('search-results');
  const chartCard = document.getElementById('search-chart-card');
  chartCard.style.display = 'none';

  if (!q) {{ container.innerHTML = '<div style="color:#999;padding:20px;text-align:center">输入关键词开始检索，如"碳排放"、"女性员工占比"、"美的集团"...</div>'; return; }}

  const results = [];
  const indicatorMatches = [];

  // 搜索指标
  DATA.indicators.forEach(ind => {{
    const text = ind.name + ' ' + (ind.description||'');
    if (text.toLowerCase().includes(q)) {{
      indicatorMatches.push(ind);
    }}
  }});

  // 搜索公司
  if (type === 'all' || type === 'company') {{
    DATA.companies.forEach(c => {{
      if (c['公司'].toLowerCase().includes(q)) {{
        const info = DATA.company_index[c['公司']];
        results.push({{type:'company', name:c['公司'], industry:c['行业'], year:c['年份'], quality:c['质量分'],
          esg: info&&info.esg_score ? info.esg_score['ESG综合'] : null }});
      }}
    }});
  }}

  // 搜索指标值
  if (type === 'all' || type === 'indicator') {{
    indicatorMatches.forEach(ind => {{
      const topCompanies = [];
      Object.entries(DATA.company_index).forEach(([name, info]) => {{
        const item = info.quantitative.find(i => i.id === ind.id);
        if (item && item.value !== null) {{
          topCompanies.push({{name, value: item.value, unit: item.unit, confidence: item.confidence}});
        }}
      }});
      topCompanies.sort((a,b) => b.value - a.value);
      results.push({{type:'indicator', id:ind.id, name:ind.name, unit:ind.unit, dimension:ind.dimension, top: topCompanies.slice(0,10)}});
    }});
  }}

  // 渲染结果
  if (results.length === 0) {{
    container.innerHTML = '<div style="color:#999;padding:12px">未找到匹配结果，请尝试其他关键词</div>';
    return;
  }}

  let html = '';
  results.forEach(r => {{
    if (r.type === 'company') {{
      html += '<div class="search-item" onclick="showCompany(\''+r.name+'\');switchTab(\'company\')">'+
        '<b>'+r.name+'</b> '+r.industry+' · '+r.year+' · ESG综合:'+(r.esg!==null?r.esg.toFixed(3):'-')+'</div>';
    }} else if (r.type === 'indicator') {{
      html += '<div class="search-item"><b>'+r.name+'</b> ('+r.unit+')<br>';
      html += '<small style="color:#888">数据TOP5: </small>';
      r.top.slice(0,5).forEach((t,i) => {{
        html += '<small>'+t.name+': <b>'+fmt(t.value,2)+'</b> '+t.unit+(i<4?' | ':'')+'</small>';
      }});
      html += '</div>';
    }}
  }});
  container.innerHTML = html;

  // 如果搜到指标且有足够数据，画图
  const indResults = results.filter(r => r.type==='indicator' && r.top.length>=2);
  if (indResults.length > 0) {{
    const r = indResults[0];
    chartCard.style.display = 'block';
    document.getElementById('search-chart-title').textContent = r.name + ' — TOP10公司';
    Plotly.newPlot('chart-search', [{{
      x: r.top.map(t=>t.name), y: r.top.map(t=>t.value),
      type: 'bar', marker: {{color: r.top.map((_,i)=>'hsl('+(i*30)+',60%,50%)')}},
      text: r.top.map(t=>fmt(t.value,2)+' '+t.unit), textposition: 'outside'
    }}], {{title: r.name+' TOP10', showlegend:false, height:400, margin:{{t:40,b:80}}}});
  }}
}}

// ====== 初始化 ======
document.addEventListener('DOMContentLoaded', function() {{
  renderOverview();
  DATA.companies.slice(0,5).forEach(c => {{
    // 预加载公司名到对比输入框的datalist
  }});
}});
</script>

</body>
</html>'''

output_path = BASE_DIR / "ESG分析系统_自包含版.html"
output_path.write_text(html, encoding="utf-8")
print(f"生成完成: {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
