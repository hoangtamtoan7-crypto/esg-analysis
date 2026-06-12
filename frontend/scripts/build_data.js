// Node.js 脚本：读取 data/output/*.json → 汇总为 public/data_pack.json
// 使用方式：node scripts/build_data.js
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '../..');
const OUTPUT_DIR = path.join(ROOT, 'data', 'output');
const ANALYSIS_DIR = path.join(ROOT, 'data', 'analysis');
const PUBLIC_DIR = path.join(__dirname, '../public');

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

function processJsonFile(filePath) {
  try {
    const raw = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    return {
      name: raw.company_name ?? '',
      industry: raw.industry ?? '',
      year: raw.report_year ?? '',
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
};

if (!fs.existsSync(PUBLIC_DIR)) fs.mkdirSync(PUBLIC_DIR, { recursive: true });
const outPath = path.join(PUBLIC_DIR, 'data_pack.json');
fs.writeFileSync(outPath, JSON.stringify(pack), 'utf-8');

const sizeKB = (fs.statSync(outPath).size / 1024).toFixed(1);
console.log(`✓ 打包完成: public/data_pack.json (${sizeKB} KB)`);
console.log(`  公司数: ${overview.companies}，报告数: ${overview.reports}，行业数: ${overview.industries}`);
