import { useState, useEffect, useCallback } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import apiClient from '../../api/client';
import type { CompanyDetail } from '../../types';

type Dimension = 'E' | 'S' | 'G';

const dimColors: Record<Dimension, string> = {
  E: '#52C41A',
  S: '#1677FF',
  G: '#FA8C16',
};
const dimLabels: Record<Dimension, string> = {
  E: '环境 (Environmental)',
  S: '社会 (Social)',
  G: '治理 (Governance)',
};

function ScoreBar({ value, color }: { value: number; color: string }) {
  const pct = Math.min(100, Math.max(0, value * 100));
  return (
    <div className="flex items-center gap-2 mt-1">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-mono text-gray-500 w-10 text-right">{value.toFixed(3)}</span>
    </div>
  );
}

function valueColor(value: number | null, allValues: (number | null)[]): string {
  if (value == null) return '';
  const nums = allValues.filter((v): v is number => v != null);
  if (nums.length < 2) return '';
  const sorted = [...nums].sort((a, b) => a - b);
  const p33 = sorted[Math.floor(sorted.length * 0.33)];
  const p66 = sorted[Math.floor(sorted.length * 0.66)];
  if (value >= p66) return 'text-[#52C41A] font-semibold';
  if (value >= p33) return 'text-[#1677FF]';
  return 'text-[#FA8C16]';
}

export default function Companies() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CompanyDetail[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<CompanyDetail | null>(null);
  const [benchmarks, setBenchmarks] = useState<{ indicator_id: string; benchmark_median?: number; industry_rank?: { total: number; rank: number; percentile: number } }[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<Dimension>('E');
  const [selectedYear, setSelectedYear] = useState<string>('');

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 1) { setResults([]); return; }
    setLoading(true);
    try {
      const res = await apiClient.get('/companies/search', { params: { q } });
      setResults(res.data);
    } catch { setResults([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => { if (query) doSearch(query); else setResults([]); }, 300);
    return () => clearTimeout(t);
  }, [query, doSearch]);

  async function selectCompany(name: string) {
    setSelected(name);
    setLoading(true);
    try {
      const [detailRes, benchRes] = await Promise.all([
        apiClient.get<CompanyDetail>(`/companies/${encodeURIComponent(name)}`),
        apiClient.get(`/benchmark/company/${encodeURIComponent(name)}`).catch(() => ({ data: { comparisons: [] } })),
      ]);
      setDetail(detailRes.data);
      setSelectedYear(detailRes.data.report_year ?? '');
      setBenchmarks(benchRes.data.comparisons || []);
    } catch { setDetail(null); setBenchmarks([]); }
    finally { setLoading(false); }
  }

  const availableYears = detail?.report_year ? [detail.report_year] : [];

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">
      <h1 className="text-2xl font-bold text-gray-900">公司详情</h1>

      {/* 搜索框 */}
      <div className="relative">
        <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSelected(null); }}
          placeholder="输入公司名称搜索..."
          className="w-full pl-11 pr-4 py-3.5 border border-gray-200 rounded-2xl focus:ring-2 focus:ring-[#1677FF] focus:border-transparent outline-none text-sm bg-white shadow-sm"
        />
        {loading && (
          <span className="absolute right-4 top-3.5 text-gray-400 text-sm">搜索中...</span>
        )}
        {results.length > 0 && !selected && (
          <div className="absolute z-20 mt-1 w-full bg-white border border-gray-200 rounded-xl shadow-lg max-h-72 overflow-auto">
            {results.map((r) => (
              <button
                key={r.name}
                onClick={() => { selectCompany(r.name); setResults([]); setQuery(r.name); }}
                className="w-full text-left px-4 py-3 hover:bg-[#1677FF]/5 border-b border-gray-50 last:border-0 cursor-pointer transition-colors"
              >
                <div className="font-medium text-gray-900">{r.name}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {r.industry} · {r.report_year} · 质量分 {r.quality_score?.toFixed(3)} · 覆盖度 {r.coverage}%
                  {r.esg_scores && (
                    <span className="ml-2 text-[#1677FF] font-medium">
                      ESG {r.esg_scores.esg_composite?.toFixed(3)}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 详情卡片 */}
      {detail && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          {/* 头部 */}
          <div className="p-6 border-b border-gray-100">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900">{detail.name}</h2>
                <p className="text-sm text-gray-500 mt-1">
                  {detail.industry} · 质量分 {detail.quality_score.toFixed(3)} · 覆盖度 {detail.coverage}%
                </p>
                {/* 年份选择器 */}
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-gray-400">报告年份</span>
                  <select
                    value={selectedYear}
                    onChange={(e) => setSelectedYear(e.target.value)}
                    className="text-sm border border-gray-200 rounded-lg px-2 py-1 focus:ring-1 focus:ring-[#1677FF] outline-none cursor-pointer"
                  >
                    {availableYears.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
              </div>
              {detail.esg_scores && (
                <div className="text-right flex-shrink-0">
                  <div className="text-3xl font-bold text-[#1677FF]">{detail.esg_scores.esg_composite.toFixed(3)}</div>
                  <div className="text-xs text-gray-400">
                    ESG综合得分 {detail.esg_scores.rank ? `#${detail.esg_scores.rank}` : ''}
                  </div>
                </div>
              )}
            </div>

            {detail.esg_scores && (
              <div className="mt-4 grid grid-cols-3 gap-3">
                {(['E', 'S', 'G'] as Dimension[]).map((dim) => {
                  const key = `${dim.toLowerCase()}_score` as 'e_score' | 's_score' | 'g_score';
                  const score = detail.esg_scores![key];
                  return (
                    <div key={dim} className="rounded-xl p-3" style={{ backgroundColor: dimColors[dim] + '15' }}>
                      <div className="text-xs text-gray-500 mb-1">{dimLabels[dim].split(' ')[0]}</div>
                      <ScoreBar value={score} color={dimColors[dim]} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* 维度 tabs */}
          <div className="border-b border-gray-100 px-6">
            <div className="flex gap-1">
              {(['E', 'S', 'G'] as Dimension[]).map((dim) => (
                <button
                  key={dim}
                  onClick={() => setTab(dim)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                    tab === dim ? 'border-current' : 'border-transparent text-gray-400 hover:text-gray-600'
                  }`}
                  style={tab === dim ? { color: dimColors[dim], borderColor: dimColors[dim] } : {}}
                >
                  {dimLabels[dim]}
                </button>
              ))}
            </div>
          </div>

          {/* 指标内容 */}
          <div className="p-6">
            {(() => {
              const qt = detail.quantitative_indicators.filter((i) => i.indicator_id.startsWith(tab));
              const ql = detail.qualitative_indicators.filter((i) => i.indicator_id.startsWith(tab));
              const allQtValues = qt.map((i) => i.value);

              return (
                <div className="space-y-6">
                  {qt.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">定量指标</h3>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="sticky top-0 bg-white">
                            <tr className="border-b border-gray-100 text-left text-xs text-gray-400 uppercase">
                              <th className="pb-2 pr-4">指标</th>
                              <th className="pb-2 pr-4">数值</th>
                              <th className="pb-2 pr-4">行业均值</th>
                              <th className="pb-2 pr-4">行业排名</th>
                              <th className="pb-2 pr-4">单位</th>
                              <th className="pb-2 pr-4">置信度</th>
                              <th className="pb-2">数据原文</th>
                            </tr>
                          </thead>
                          <tbody>
                            {qt.map((item, i) => {
                              const bm = benchmarks.find((b) => b.indicator_id === item.indicator_id);
                              const colorClass = valueColor(item.value, allQtValues);
                              return (
                                <tr
                                  key={i}
                                  className={`border-b border-gray-50 hover:bg-[#1677FF]/5 transition-colors ${
                                    i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'
                                  }`}
                                >
                                  <td className="py-2 pr-4 font-medium text-gray-800">{item.indicator_name}</td>
                                  <td className={`py-2 pr-4 font-mono ${colorClass}`}>
                                    {item.value != null ? item.value.toLocaleString() : '-'}
                                  </td>
                                  <td className="py-2 pr-4 text-xs text-gray-500">
                                    {bm?.benchmark_median?.toLocaleString() ?? '-'}
                                  </td>
                                  <td className="py-2 pr-4">
                                    {bm?.industry_rank ? (
                                      <span className={`text-xs ${
                                        bm.industry_rank.percentile <= 25 ? 'text-[#52C41A] font-medium' :
                                        bm.industry_rank.percentile >= 75 ? 'text-[#FF4D4F] font-medium' : 'text-gray-500'
                                      }`}>
                                        #{bm.industry_rank.rank}/{bm.industry_rank.total} (前{bm.industry_rank.percentile}%)
                                      </span>
                                    ) : '-'}
                                  </td>
                                  <td className="py-2 pr-4 text-gray-500">{item.unit || '-'}</td>
                                  <td className="py-2 pr-4">
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                      item.confidence === 'high' ? 'bg-green-100 text-green-700' :
                                      item.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                      'bg-red-100 text-red-700'
                                    }`}>
                                      {item.confidence}
                                    </span>
                                  </td>
                                  <td className="py-2 text-gray-500 max-w-xs truncate text-xs">{item.original_text || '-'}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {ql.length > 0 && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-3">定性指标</h3>
                      <div className="space-y-2">
                        {ql.map((item, i) => (
                          <div
                            key={i}
                            className={`border rounded-xl p-4 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'} border-gray-100`}
                          >
                            <div className="flex items-center gap-2 mb-1.5">
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                item.status === 'yes' ? 'bg-green-100 text-green-700' :
                                item.status === 'no' ? 'bg-red-100 text-red-700' :
                                'bg-yellow-100 text-yellow-700'
                              }`}>
                                {item.status === 'yes' ? '是' : item.status === 'no' ? '否' : '部分'}
                              </span>
                              <span className="font-medium text-gray-800 text-sm">{item.indicator_name}</span>
                              <span className={`px-2 py-0.5 rounded-full text-xs ${
                                item.confidence === 'high' ? 'bg-green-100 text-green-700' :
                                item.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                              }`}>
                                {item.confidence}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600">{item.summary}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {qt.length === 0 && ql.length === 0 && (
                    <div className="text-center py-12">
                      <div className="text-gray-300 text-4xl mb-3">—</div>
                      <p className="text-gray-400">该维度暂无数据</p>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {!detail && !loading && query.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 py-20 text-center">
          <MagnifyingGlassIcon className="h-12 w-12 text-gray-200 mx-auto mb-3" />
          <p className="text-gray-400">请输入公司名称进行搜索</p>
        </div>
      )}
    </div>
  );
}
