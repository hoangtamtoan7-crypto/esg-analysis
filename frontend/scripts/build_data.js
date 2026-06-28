// Node.js 脚本：读取 data/output/*.json → 汇总为 public/data_pack.json
// 使用方式：node scripts/build_data.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const OUTPUT_DIR = process.env.ESG_OUTPUT_DIR || path.join(ROOT, 'data', 'output');
const ANALYSIS_DIR = path.join(ROOT, 'data', 'analysis');
const PUBLIC_DIR = path.join(__dirname, '../public');
const HUAZHENG_TREND_PATH = path.join(ANALYSIS_DIR, 'huazheng_esg_quarterly.json');

function readCSV(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map((h) => h.trim());
  return lines.slice(1).map((line) => {
    const vals = line.split(',');
    const row = {};
    headers.forEach((h, i) => {
      const v = vals[i]?.trim() ?? '';
      row[h] = isNaN(Number(v)) || v === '' ? v : Number(v);
    });
    return row;
  });
}

function parseFileMeta(filePath) {
  const fileName = path.basename(filePath);
  const standard = fileName.match(/^(\d{6})_(.+?)_(\d{4})_result\.json$/);
  if (standard) {
    return { stock_code: standard[1], file_company: standard[2], file_year: standard[3] };
  }
  const code = fileName.match(/^(\d{6})_/);
  const year = fileName.match(/_(19\d{2}|20\d{2})_/);
  return {
    stock_code: code?.[1] ?? '',
    file_company: '',
    file_year: year?.[1] ?? '',
  };
}

function processJsonFile(filePath) {
  try {
    const raw = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    const meta = parseFileMeta(filePath);
    return {
      stock_code: meta.stock_code,
      name: raw.company_name ?? '',
      industry: raw.industry ?? '',
      year: String(raw.report_year ?? meta.file_year ?? ''),
      quality_score: raw.quality_score ?? 0,
      coverage: raw.coverage ?? 0,
      esg_scores: raw.esg_scores ?? null,
      quantitative_indicators: (raw.quantitative_indicators ?? []).map((ind) => ({
        indicator_id: ind.id ?? ind.indicator_id ?? '',
        indicator_name: ind.name ?? ind.indicator_name ?? '',
        value: ind.value ?? null,
        unit: ind.unit ?? '',
        confidence: ind.confidence ?? 'low',
      })),
      qualitative_indicators: (raw.qualitative_indicators ?? []).map((ind) => ({
        indicator_id: ind.id ?? ind.indicator_id ?? '',
        indicator_name: ind.name ?? ind.indicator_name ?? '',
        status: ind.status ?? 'no',
        summary: ind.summary ?? '',
        confidence: ind.confidence ?? 'low',
      })),
    };
  } catch (e) {
    console.warn(`跳过文件 ${path.basename(filePath)}: ${e.message}`);
    return null;
  }
}

function readHuazhengRows() {
  if (!fs.existsSync(HUAZHENG_TREND_PATH)) return [];
  try {
    return JSON.parse(fs.readFileSync(HUAZHENG_TREND_PATH, 'utf-8'));
  } catch (e) {
    console.warn(`读取华证趋势数据失败: ${e.message}`);
    return [];
  }
}

function mean(values) {
  const nums = values.filter((v) => typeof v === 'number' && Number.isFinite(v));
  if (!nums.length) return null;
  return nums.reduce((s, v) => s + v, 0) / nums.length;
}

function round(value, digits = 2) {
  if (value == null || !Number.isFinite(value)) return null;
  const base = 10 ** digits;
  return Math.round(value * base) / base;
}

function makePoint(year, value, extras = {}) {
  return { year: String(year), value: value == null ? null : round(value, 4), ...extras };
}

function buildTrendInsights(company, ratingPoints, indicatorTrends) {
  const insights = [];
  const composite = ratingPoints['ESG综合'] ?? [];
  if (composite.length >= 2) {
    const first = composite[0];
    const last = composite[composite.length - 1];
    const delta = round(last.value - first.value, 2);
    insights.push({
      type: delta >= 0 ? '评级改善' : '评级回落',
      text: `${company} 华证ESG综合得分从 ${first.year} 年 ${round(first.value, 2)} 变为 ${last.year} 年 ${round(last.value, 2)}，变化 ${delta > 0 ? '+' : ''}${delta} 分。`,
    });
  }

  const dims = ['E', 'S', 'G']
    .map((key) => {
      const pts = ratingPoints[key] ?? [];
      if (pts.length < 2) return null;
      return { key, delta: pts[pts.length - 1].value - pts[0].value };
    })
    .filter(Boolean)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
  if (dims.length) {
    const top = dims[0];
    insights.push({
      type: '维度波动',
      text: `${top.key} 维度是区间内变化最大的评级维度，累计变化 ${top.delta >= 0 ? '+' : ''}${round(top.delta, 2)} 分。`,
    });
  }

  const indicator = Object.entries(indicatorTrends)
    .map(([name, pts]) => ({ name, pts: pts.filter((p) => p.value != null) }))
    .filter((x) => x.pts.length >= 2)
    .sort((a, b) => b.pts.length - a.pts.length)[0];
  if (indicator) {
    const first = indicator.pts[0];
    const last = indicator.pts[indicator.pts.length - 1];
    const delta = round(last.value - first.value, 2);
    insights.push({
      type: '抽取指标',
      text: `${indicator.name} 已形成 ${indicator.pts.length} 个年度观测点，从 ${first.year} 年到 ${last.year} 年变化 ${delta > 0 ? '+' : ''}${delta}。`,
    });
  }

  return insights;
}

function buildTrendAnalysis(companies, huazhengRows) {
  const reportsByCode = new Map();
  const reportsByName = new Map();
  for (const report of companies) {
    if (report.stock_code) {
      if (!reportsByCode.has(report.stock_code)) reportsByCode.set(report.stock_code, []);
      reportsByCode.get(report.stock_code).push(report);
    }
    if (report.name) {
      if (!reportsByName.has(report.name)) reportsByName.set(report.name, []);
      reportsByName.get(report.name).push(report);
    }
  }

  const ratingByCodeYear = new Map();
  for (const row of huazhengRows) {
    const code = row.stock_code;
    const year = String(row.year ?? '').trim();
    if (!code || !year) continue;
    const key = `${code}|${year}`;
    if (!ratingByCodeYear.has(key)) ratingByCodeYear.set(key, []);
    ratingByCodeYear.get(key).push(row);
  }

  const annualRatings = new Map();
  for (const [key, rows] of ratingByCodeYear.entries()) {
    const [code, year] = key.split('|');
    const latest = rows.slice().sort((a, b) => String(a.date).localeCompare(String(b.date))).at(-1);
    const item = {
      stock_code: code,
      year,
      company: latest?.company ?? '',
      industry: latest?.industry_cs ?? latest?.industry_ths ?? latest?.industry_sw ?? '',
      rating: latest?.rating ?? '',
      e_rating: latest?.e_rating ?? '',
      s_rating: latest?.s_rating ?? '',
      g_rating: latest?.g_rating ?? '',
      composite_score: round(mean(rows.map((r) => r.composite_score)), 2),
      e_score: round(mean(rows.map((r) => r.e_score)), 2),
      s_score: round(mean(rows.map((r) => r.s_score)), 2),
      g_score: round(mean(rows.map((r) => r.g_score)), 2),
      quarters: rows.length,
    };
    if (!annualRatings.has(code)) annualRatings.set(code, []);
    annualRatings.get(code).push(item);
  }
  for (const items of annualRatings.values()) {
    items.sort((a, b) => a.year.localeCompare(b.year));
  }

  const keyIndicatorIds = new Set(['E_Q01', 'E_Q04', 'E_Q06', 'E_Q07', 'S_Q01', 'S_Q02', 'S_Q05', 'S_Q06', 'S_Q08', 'G_Q02', 'G_Q04']);
  const companyTrends = [];
  const allCodes = new Set([...reportsByCode.keys()]);
  for (const code of allCodes) {
    const reports = (reportsByCode.get(code) ?? []).slice().sort((a, b) => a.year.localeCompare(b.year));
    const annual = annualRatings.get(code) ?? [];
    const name = annual.at(-1)?.company || reports.at(-1)?.name || '';
    if (!name) continue;
    const industry = annual.at(-1)?.industry || reports.at(-1)?.industry || '';
    const ratingTrend = {
      E: annual.map((r) => makePoint(r.year, r.e_score, { rating: r.e_rating, quarters: r.quarters })),
      S: annual.map((r) => makePoint(r.year, r.s_score, { rating: r.s_rating, quarters: r.quarters })),
      G: annual.map((r) => makePoint(r.year, r.g_score, { rating: r.g_rating, quarters: r.quarters })),
      ESG综合: annual.map((r) => makePoint(r.year, r.composite_score, { rating: r.rating, quarters: r.quarters })),
    };

    const indicatorMap = new Map();
    for (const report of reports) {
      for (const ind of report.quantitative_indicators ?? []) {
        if (!keyIndicatorIds.has(ind.indicator_id) || ind.value == null || !Number.isFinite(Number(ind.value))) continue;
        const key = ind.indicator_name || ind.indicator_id;
        if (!indicatorMap.has(key)) {
          indicatorMap.set(key, { unit: ind.unit ?? '', points: [] });
        }
        indicatorMap.get(key).points.push(makePoint(report.year, Number(ind.value), {
          unit: ind.unit ?? '',
          confidence: ind.confidence ?? '',
        }));
      }
    }

    const indicatorTrends = {};
    for (const [indicatorName, item] of indicatorMap.entries()) {
      const byYear = new Map();
      for (const pt of item.points) byYear.set(pt.year, pt);
      const points = [...byYear.values()].sort((a, b) => a.year.localeCompare(b.year));
      if (points.length >= 1) indicatorTrends[indicatorName] = points;
    }

    companyTrends.push({
      stock_code: code,
      company: name,
      industry,
      report_years: reports.map((r) => r.year),
      rating_years: annual.map((r) => r.year),
      esg_trend: ratingTrend,
      indicator_trends: indicatorTrends,
      insights: buildTrendInsights(name, ratingTrend, indicatorTrends),
    });
  }

  const industryBucket = new Map();
  for (const item of companyTrends) {
    const industry = item.industry || '未分类';
    for (const pt of item.esg_trend['ESG综合'] ?? []) {
      if (pt.value == null) continue;
      const key = `${industry}|${pt.year}`;
      if (!industryBucket.has(key)) industryBucket.set(key, []);
      industryBucket.get(key).push(pt.value);
    }
  }
  const industryTrends = {};
  for (const [key, values] of industryBucket.entries()) {
    const [industry, year] = key.split('|');
    if (!industryTrends[industry]) industryTrends[industry] = [];
    industryTrends[industry].push({ year, value: round(mean(values), 2), company_count: values.length });
  }
  Object.values(industryTrends).forEach((pts) => pts.sort((a, b) => a.year.localeCompare(b.year)));

  return {
    source: '华证ESG季度评级 + LLM抽取JSON',
    rating_records: huazhengRows.length,
    companies: companyTrends.sort((a, b) => a.stock_code.localeCompare(b.stock_code)),
    industry_trends: industryTrends,
  };
}

// 主逻辑
if (!fs.existsSync(OUTPUT_DIR)) {
  console.error('data/output 目录不存在:', OUTPUT_DIR);
  process.exit(1);
}

// 从 esg_scores.csv 构建公司→行业映射
const esgScoresRaw = readCSV(path.join(ANALYSIS_DIR, 'esg_scores.csv'));
const industryMap = {};
for (const row of esgScoresRaw) {
  const name = row['公司'] ?? row['company'] ?? '';
  const ind = row['行业'] ?? row['industry'] ?? '';
  if (name && ind) industryMap[name] = ind;
}

const jsonFiles = fs.readdirSync(OUTPUT_DIR).filter((f) => f.endsWith('_result.json'));
console.log(`找到 ${jsonFiles.length} 个 JSON 文件，开始打包...`);

const companies = [];
for (const file of jsonFiles) {
  const data = processJsonFile(path.join(OUTPUT_DIR, file));
  if (data && data.name) {
    // 从映射中补充行业信息
    if (!data.industry && industryMap[data.name]) {
      data.industry = industryMap[data.name];
    }
    companies.push(data);
  }
}

const esgScores = readCSV(path.join(ANALYSIS_DIR, 'esg_scores.csv'));
const industryAnalysis = readCSV(path.join(ANALYSIS_DIR, 'industry_analysis.csv'));
const huazhengRows = readHuazhengRows();
const trendAnalysis = buildTrendAnalysis(companies, huazhengRows);

// 概览统计
const industrySet = new Set(companies.map((c) => c.industry).filter(Boolean));
const industryDistribution = [...industrySet].map((ind) => ({
  industry: ind,
  count: companies.filter((c) => c.industry === ind).length,
})).sort((a, b) => b.count - a.count);

const overview = {
  companies: new Set(companies.map((c) => c.name)).size,
  reports: companies.length,
  industries: industrySet.size,
  avg_quality_score: companies.length
    ? companies.reduce((s, c) => s + (c.quality_score ?? 0), 0) / companies.length
    : 0,
  quantitative_indicators: companies[0]?.quantitative_indicators?.length ?? 0,
  qualitative_indicators: companies[0]?.qualitative_indicators?.length ?? 0,
  industry_distribution: industryDistribution,
};

const pack = {
  generated_at: new Date().toISOString(),
  overview,
  companies,
  esg_scores: esgScores,
  industry_analysis: industryAnalysis,
  trend_analysis: trendAnalysis,
};

if (!fs.existsSync(PUBLIC_DIR)) fs.mkdirSync(PUBLIC_DIR, { recursive: true });
const outPath = path.join(PUBLIC_DIR, 'data_pack.json');
fs.writeFileSync(outPath, JSON.stringify(pack), 'utf-8');

const sizeKB = (fs.statSync(outPath).size / 1024).toFixed(1);
console.log(`✓ 打包完成: public/data_pack.json (${sizeKB} KB)`);
console.log(`  公司数: ${overview.companies}，报告数: ${overview.reports}，行业数: ${overview.industries}`);
console.log(`  趋势公司数: ${trendAnalysis.companies.length}，华证评级记录: ${trendAnalysis.rating_records}`);
