import type { OverviewData, ESGScoreRow, IndustryRow, TrendAnalysis } from '../types';

interface CompanyRecord {
  stock_code?: string;
  name: string;
  industry: string;
  year: string;
  quality_score: number;
  coverage: number;
  esg_scores: {
    rank?: number;
    e_score: number;
    s_score: number;
    g_score: number;
    esg_composite: number;
  } | null;
  quantitative_indicators: {
    indicator_id: string;
    indicator_name: string;
    value: number | null;
    unit: string;
    confidence: string;
  }[];
  qualitative_indicators: {
    indicator_id: string;
    indicator_name: string;
    status: 'yes' | 'no' | 'partial';
    summary: string;
    confidence: string;
  }[];
}

interface DataPack {
  generated_at: string;
  overview: OverviewData;
  companies: CompanyRecord[];
  esg_scores: ESGScoreRow[];
  industry_analysis: IndustryRow[];
  trend_analysis?: TrendAnalysis;
}

let cachedData: DataPack | null = null;

export async function loadData(): Promise<DataPack> {
  if (cachedData) return cachedData;
  const resp = await fetch('/data_pack.json');
  if (!resp.ok) throw new Error(`加载数据失败: ${resp.status}`);
  cachedData = await resp.json() as DataPack;
  return cachedData;
}

export function getOverview(data: DataPack): OverviewData {
  return data.overview;
}

export function getCompanies(data: DataPack): string[] {
  return [...new Set(data.companies.map((c) => c.name))];
}

export function getScores(data: DataPack): ESGScoreRow[] {
  return data.esg_scores ?? [];
}

export function getIndustries(data: DataPack): IndustryRow[] {
  return data.industry_analysis ?? [];
}

export function getCompanyDetail(data: DataPack, name: string): CompanyRecord | undefined {
  return data.companies.find((c) => c.name === name);
}

export function searchCompanies(data: DataPack, query: string): CompanyRecord[] {
  const q = query.toLowerCase();
  return data.companies.filter((c) => c.name.toLowerCase().includes(q)).slice(0, 20);
}

export function getIndustryList(data: DataPack): string[] {
  return [...new Set(data.companies.map((c) => c.industry).filter(Boolean))];
}

export function getTrendAnalysis(data: DataPack): TrendAnalysis | undefined {
  return data.trend_analysis;
}
