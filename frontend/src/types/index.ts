// ---- 公司 ----
export interface Company {
  stock_code: string;
  name: string;
  exchange?: string;
  market?: string;
  industry?: string;
}

export interface CompanyDetail extends Company {
  report_year: string;
  quality_score: number;
  coverage: number;
  esg_scores?: ESGScores;
  quantitative_indicators: IndicatorValue[];
  qualitative_indicators: QualitativeValue[];
}

export interface ESGScores {
  rank?: number;
  e_score: number;
  s_score: number;
  g_score: number;
  esg_composite: number;
}

// ---- 指标 ----
export type Dimension = 'E' | 'S' | 'G';
export type IndicatorType = 'quantitative' | 'qualitative';

export interface Indicator {
  id: string;
  name: string;
  name_en?: string;
  dimension: Dimension;
  indicator_type: IndicatorType;
  unit?: string;
  keywords: string[];
  description?: string;
}

export interface IndicatorValue {
  indicator_id: string;
  indicator_name: string;
  value: number | null;
  unit: string;
  confidence: string;
  original_text?: string;
}

export interface QualitativeValue {
  indicator_id: string;
  indicator_name: string;
  status: 'yes' | 'no' | 'partial';
  summary: string;
  confidence: string;
  original_text?: string;
}

// ---- 分析 ----
export interface ESGScoreRow {
  排名: number;
  公司: string;
  行业: string;
  E_得分: number;
  S_得分: number;
  G_得分: number;
  ESG综合: number;
}

export interface IndustryRow {
  行业: string;
  公司数: number;
  平均碳排放_吨: number | null;
  平均可再生比例_pct: number | null;
  平均女性员工_pct: number | null;
  平均研发占比_pct: number | null;
}

export interface Insight {
  类别: string;
  洞察: string;
}

export interface DimensionDistribution {
  dimension: Dimension;
  name: string;
  mean: number;
  bins: { center: number; count: number }[];
}

// ---- 概览 ----
export interface OverviewData {
  companies: number;
  reports: number;
  industries: number;
  avg_quality_score: number;
  quantitative_indicators: number;
  qualitative_indicators: number;
  industry_distribution: { industry: string; count: number }[];
}

// ---- AI 对话 ----
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  tables?: TableData[];
  tool_calls?: ToolCall[];
}

export interface TableData {
  title?: string;
  headers: string[];
  rows: (string | number | null)[][];
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

// ---- 数据导出 ----
export interface DataStats {
  companies: number;
  reports: number;
  reports_done: number;
  extracted_values: number;
  extracted_texts: number;
}

// ---- 趋势分析 ----
export interface TrendPoint {
  year: string;
  value: number | null;
}

export interface CompanyTrend {
  company: string;
  industry: string;
  esg_trend: Record<string, TrendPoint[]>;
  indicator_trends: Record<string, TrendPoint[]>;
}

// ---- 行业对标 ----
export interface IndustryBenchmark {
  industry: string;
  company_count: number;
  indicator_id: string;
  indicator_name: string;
  unit: string;
  mean: number;
  median: number;
  p25: number;
  p75: number;
  min_val?: number;
  max_val?: number;
}

export interface CompanyBenchmark {
  indicator_id: string;
  indicator_name: string;
  company_value: number;
  unit: string;
  benchmark_median: number;
  benchmark_mean: number;
  benchmark_p25: number;
  benchmark_p75: number;
  industry_rank?: { total: number; rank: number; percentile: number };
}

// ---- 投资筛选 ----
export interface ScreenRequest {
  conditions?: { indicator_id: string; op: string; value: number }[];
  esg_e_min?: number;
  esg_s_min?: number;
  esg_g_min?: number;
  esg_composite_min?: number;
  industry?: string;
  quality_min?: number;
  limit?: number;
}

// ---- 合规分析 ----
export interface ComplianceItem {
  indicator_id: string;
  indicator_name: string;
  dimension: string;
  indicator_type: string;
  disclosure_rate: number;
  industry_breakdown: { industry: string; companies_with_data: number; disclosure_rate: number }[];
}

// ---- 筛选元数据 ----
export interface FilterMetadata {
  industries: string[];
  years: string[];
  dimensions: string[];
  indicator_types: string[];
  total_companies: number;
  total_indicators: number;
}
