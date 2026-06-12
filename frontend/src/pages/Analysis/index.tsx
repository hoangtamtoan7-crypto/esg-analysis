import { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../api/client';
import type { ESGScoreRow, IndustryRow, Insight, DimensionDistribution } from '../../types';

export default function Analysis() {
  const [scores, setScores] = useState<ESGScoreRow[]>([]);
  const [industries, setIndustries] = useState<IndustryRow[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [dists, setDists] = useState<DimensionDistribution[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiClient.get('/analysis/esg-scores', { params: { top_n: 50 } }),
      apiClient.get('/analysis/industries'),
      apiClient.get('/analysis/insights'),
      apiClient.get('/analysis/distributions'),
    ]).then(([s, i, ins, d]) => {
      setScores(s.data);
      setIndustries(i.data);
      setInsights(ins.data);
      setDists(d.data);
    }).catch(() => {})
    .finally(() => setLoading(false));
  }, []);

  // ESG ranking chart
  const rankOption = useMemo(() => {
    const top10 = [...scores].slice(0, 10).reverse();
    if (!top10.length) return {};
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 100, right: 40, top: 10, bottom: 20 },
      xAxis: { type: 'value', name: 'ESG综合得分', max: 1.05 },
      yAxis: { type: 'category', data: top10.map((r) => r['公司']) },
      series: [{
        type: 'bar',
        data: top10.map((r, i) => ({
          value: r['ESG综合'],
          itemStyle: {
            color: `rgba(67, 56, 202, ${0.3 + 0.7 * (i / top10.length)})`,
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: { show: true, position: 'right', formatter: (p: any) => p.value.toFixed(3) },
      }],
    };
  }, [scores]);

  // Dimension distributions chart options
  const dimColors: Record<string, string> = { E: '#2e7d32', S: '#1565c0', G: '#e65100' };

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">ESG综合分析</h1>

      {loading ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">加载分析数据中...</div>
      ) : (
        <>
          {/* ESG Ranking */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">ESG综合排名 TOP20</h2>
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <div className="lg:col-span-3 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-left text-xs text-gray-400 uppercase">
                      <th className="pb-2">排名</th>
                      <th className="pb-2">公司</th>
                      <th className="pb-2">行业</th>
                      <th className="pb-2">E得分</th>
                      <th className="pb-2">S得分</th>
                      <th className="pb-2">G得分</th>
                      <th className="pb-2">ESG综合</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scores.slice(0, 20).map((row, i) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 text-gray-500">{row['排名']}</td>
                        <td className="py-2 font-medium text-gray-900">{row['公司']}</td>
                        <td className="py-2 text-gray-500">{row['行业']}</td>
                        <td className="py-2 font-mono text-gray-800">{row['E_得分'].toFixed(3)}</td>
                        <td className="py-2 font-mono text-gray-800">{row['S_得分'].toFixed(3)}</td>
                        <td className="py-2 font-mono text-gray-800">{row['G_得分'].toFixed(3)}</td>
                        <td className="py-2 font-mono font-semibold text-primary-700">{row['ESG综合'].toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="lg:col-span-2">
                <ReactECharts option={rankOption} style={{ height: 400 }} />
              </div>
            </div>
          </div>

          {/* Dimension Distributions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {dists.map((dist) => {
              const color = dimColors[dist.dimension] || '#6366f1';
              const bins = dist.bins;
              const option = {
                tooltip: { trigger: 'axis' },
                grid: { left: 40, right: 20, top: 30, bottom: 30 },
                xAxis: { type: 'category', data: bins.map((b) => b.center.toFixed(2)), axisLabel: { rotate: 45, fontSize: 9 } },
                yAxis: { type: 'value', name: '公司数' },
                series: [{
                  type: 'bar',
                  data: bins.map((b) => ({
                    value: b.count,
                    itemStyle: {
                      color,
                      borderRadius: [3, 3, 0, 0],
                      opacity: 0.85,
                    },
                  })),
                  barWidth: '85%',
                }],
              };
              return (
                <div key={dist.dimension} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                  <h3 className="text-sm font-semibold text-gray-900 mb-1">{dist.name}</h3>
                  <p className="text-xs text-gray-400 mb-2">均值: {dist.mean.toFixed(3)}</p>
                  <ReactECharts option={option} style={{ height: 200 }} />
                </div>
              );
            })}
          </div>

          {/* Industry Analysis */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">行业ESG对比</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-left text-xs text-gray-400 uppercase">
                      <th className="pb-2">行业</th>
                      <th className="pb-2">公司数</th>
                      <th className="pb-2">平均碳排放(吨)</th>
                      <th className="pb-2">可再生(%)</th>
                      <th className="pb-2">女性员工(%)</th>
                      <th className="pb-2">研发占比(%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {industries.map((row, i) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="py-2 font-medium text-gray-900">{row['行业']}</td>
                        <td className="py-2 text-gray-500">{row['公司数']}</td>
                        <td className="py-2 font-mono text-gray-800">{row['平均碳排放_吨']?.toLocaleString() ?? '-'}</td>
                        <td className="py-2 font-mono text-gray-800">{row['平均可再生比例_pct']?.toFixed(1) ?? '-'}</td>
                        <td className="py-2 font-mono text-gray-800">{row['平均女性员工_pct']?.toFixed(1) ?? '-'}</td>
                        <td className="py-2 font-mono text-gray-800">{row['平均研发占比_pct']?.toFixed(2) ?? '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                {(() => {
                  const carbonData = industries
                    .filter((r) => r['平均碳排放_吨'] != null)
                    .sort((a, b) => (a['平均碳排放_吨'] || 0) - (b['平均碳排放_吨'] || 0));
                  if (!carbonData.length) return null;
                  const opt = {
                    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                    grid: { left: 80, right: 20, top: 10, bottom: 20 },
                    xAxis: { type: 'value', name: '吨' },
                    yAxis: { type: 'category', data: carbonData.map((r) => r['行业']) },
                    series: [{
                      type: 'bar',
                      data: carbonData.map((r, i) => ({
                        value: r['平均碳排放_吨'],
                        itemStyle: {
                          color: `rgba(239, 68, 68, ${0.3 + 0.7 * (i / carbonData.length)})`,
                          borderRadius: [0, 4, 4, 0],
                        },
                      })),
                      label: { show: true, position: 'right', formatter: (p: any) => p.value?.toLocaleString() || '' },
                    }],
                  };
                  return <ReactECharts option={opt} style={{ height: Math.max(300, carbonData.length * 30) }} />;
                })()}
              </div>
            </div>
          </div>

          {/* Insights */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">关键数据洞察</h2>
            <div className="space-y-3">
              {insights.map((ins, i) => (
                <div key={i} className="flex gap-3 items-start p-3 bg-blue-50 rounded-lg">
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 whitespace-nowrap mt-0.5">
                    {ins['类别']}
                  </span>
                  <p className="text-sm text-gray-700">{ins['洞察']}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Investment Screening */}
          <InvestmentScreening industries={industries.map((r) => r['行业'])} />
        </>
      )}
    </div>
  );
}

type ScreenResult = { 公司: string; 行业: string; E_得分: number; S_得分: number; G_得分: number; ESG综合: number; 排名: number };

function InvestmentScreening({ industries }: { industries: string[] }) {
  const [esgMin, setEsgMin] = useState(0);
  const [industry, setIndustry] = useState('');
  const [results, setResults] = useState<ScreenResult[]>([]);
  const [screening, setScreening] = useState(false);

  async function doScreen() {
    setScreening(true);
    try {
      const body: any = { limit: 20 };
      if (esgMin > 0) body.esg_composite_min = esgMin;
      if (industry) body.industry = industry;
      const res = await apiClient.post('/investment/screen', body);
      setResults(res.data.companies || []);
    } catch { setResults([]); }
    finally { setScreening(false); }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">投资筛选</h2>
      <div className="flex flex-wrap gap-3 mb-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">ESG综合最低分</label>
          <input type="range" min="0" max="100" value={Math.round(esgMin * 100)} onChange={(e) => setEsgMin(Number(e.target.value) / 100)}
            className="w-40" />
          <span className="text-sm font-mono ml-2">{(esgMin).toFixed(2)}</span>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">行业</label>
          <select value={industry} onChange={(e) => setIndustry(e.target.value)}
            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm">
            <option value="">全部行业</option>
            {industries.filter(Boolean).map((ind) => <option key={ind} value={ind}>{ind}</option>)}
          </select>
        </div>
        <div className="flex items-end">
          <button onClick={doScreen} disabled={screening}
            className="px-4 py-1.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-40">
            {screening ? '筛选中...' : '开始筛选'}
          </button>
        </div>
      </div>

      {results.length > 0 && (
        <div className="overflow-x-auto">
          <p className="text-xs text-gray-400 mb-2">符合条件: {results.length} 家公司</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-gray-400 uppercase">
                <th className="pb-2">排名</th><th className="pb-2">公司</th><th className="pb-2">行业</th>
                <th className="pb-2">E得分</th><th className="pb-2">S得分</th><th className="pb-2">G得分</th><th className="pb-2">ESG综合</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 text-gray-500">{r['排名']}</td>
                  <td className="py-2 font-medium text-gray-900">{r['公司']}</td>
                  <td className="py-2 text-gray-500">{r['行业']}</td>
                  <td className="py-2 font-mono text-gray-800">{r['E_得分'].toFixed(3)}</td>
                  <td className="py-2 font-mono text-gray-800">{r['S_得分'].toFixed(3)}</td>
                  <td className="py-2 font-mono text-gray-800">{r['G_得分'].toFixed(3)}</td>
                  <td className="py-2 font-mono font-semibold text-primary-700">{r['ESG综合'].toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
