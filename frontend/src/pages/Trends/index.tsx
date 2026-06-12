import { useState, useEffect, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../api/client';
import type { CompanyTrend } from '../../types';

export default function Trends() {
  const [companies, setCompanies] = useState<string[]>([]);
  const [selected, setSelected] = useState('');
  const [trend, setTrend] = useState<CompanyTrend | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiClient.get('/companies').then((res) => {
      setCompanies(res.data.map((c: any) => c.name));
    }).catch(() => {});
  }, []);

  const loadTrend = useCallback(async (name: string) => {
    setSelected(name);
    setLoading(true);
    try {
      const res = await apiClient.get(`/trends/company/${encodeURIComponent(name)}`);
      setTrend(res.data);
    } catch { setTrend(null); }
    finally { setLoading(false); }
  }, []);

  // ESG score trend chart
  const esgChartOption = () => {
    if (!trend) return {};
    const esg = trend.esg_trend;
    const allYears = new Set<string>();
    Object.values(esg).forEach((pts) => pts.forEach((p) => allYears.add(p.year)));
    const years = [...allYears].sort();

    const dimColors: Record<string, string> = { E: '#2e7d32', S: '#1565c0', G: '#e65100', ESG综合: '#6366f1' };
    return {
      tooltip: { trigger: 'axis' },
      legend: { data: Object.keys(esg), top: 0 },
      grid: { left: 50, right: 20, top: 40, bottom: 30 },
      xAxis: { type: 'category', data: years, boundaryGap: false },
      yAxis: { type: 'value', min: 0, max: 1.1, name: '得分' },
      series: Object.entries(esg).map(([key, pts]) => {
        const data = years.map((yr) => {
          const pt = pts.find((p) => p.year === yr);
          return pt?.value ?? null;
        });
        return { name: key, type: 'line', data, color: dimColors[key] || '#888', smooth: true, symbol: 'circle', symbolSize: 8 };
      }),
    };
  };

  const dataNote = trend
    ? (Object.values(trend.esg_trend).flat().length <= 4 ? '当前数据年度较少，折线图仅为已有数据的可视化展示。随着多年度报告数据积累，趋势分析将更加丰富。' : '')
    : '';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">趋势分析</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <select
          value={selected}
          onChange={(e) => loadTrend(e.target.value)}
          className="w-full md:w-96 px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">选择公司查看ESG趋势...</option>
          {companies.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        {trend && <p className="text-xs text-gray-400 mt-2">{trend.company} · {trend.industry} · 跨年度ESG表现</p>}
      </div>

      {loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">加载趋势数据...</div>
      )}

      {trend && (
        <>
          {dataNote && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-700">
              {dataNote}
            </div>
          )}

          {/* ESG Score Trend */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{trend.company} ESG得分趋势</h2>
            <ReactECharts option={esgChartOption()} style={{ height: 400 }} />
          </div>

          {/* Indicator mini-trends */}
          {Object.keys(trend.indicator_trends).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">关键指标趋势</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(trend.indicator_trends).map(([name, pts]) => {
                  const data = pts.sort((a, b) => a.year.localeCompare(b.year));
                  const opt = {
                    tooltip: { trigger: 'axis' },
                    grid: { left: 60, right: 20, top: 30, bottom: 25 },
                    xAxis: { type: 'category', data: data.map((p) => p.year) },
                    yAxis: { type: 'value', name: '' },
                    series: [{
                      type: 'line', data: data.map((p) => p.value),
                      smooth: true, symbol: 'circle', symbolSize: 6,
                      areaStyle: { opacity: 0.15 },
                      itemStyle: { color: '#6366f1' },
                    }],
                  };
                  return (
                    <div key={name} className="border border-gray-100 rounded-lg p-3">
                      <h3 className="text-sm font-medium text-gray-700 mb-1">{name}</h3>
                      <ReactECharts option={opt} style={{ height: 200 }} />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {!trend && !loading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          <p className="text-lg">选择公司查看跨年度趋势</p>
          <p className="text-sm mt-2">趋势分析需要多年度数据 — 请使用 `python run.py download` 下载更多历史年度报告</p>
          <p className="text-xs mt-1 text-gray-300">默认下载年份范围: 2019-2026</p>
        </div>
      )}
    </div>
  );
}
