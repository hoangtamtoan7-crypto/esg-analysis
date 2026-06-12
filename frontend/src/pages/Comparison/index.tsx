import { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../api/client';
import { useComparisonBasket } from '../../stores/comparisonStore';
import type { Indicator } from '../../types';

type DimFilter = '全部' | 'E' | 'S' | 'G';
type Mode = 'single' | 'matrix';

export default function Comparison() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [dimFilter, setDimFilter] = useState<DimFilter>('全部');
  const [selectedId, setSelectedId] = useState<string>('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [meta, setMeta] = useState({ unit: '', name: '', count: 0, description: '' });
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<Mode>('single');

  // Matrix mode state
  const { indicatorIds, companyNames, addIndicator, removeIndicator, addCompany, removeCompany, clearAll } = useComparisonBasket();
  const [matrixData, setMatrixData] = useState<any>(null);
  const [companySearch, setCompanySearch] = useState('');

  useEffect(() => {
    apiClient.get('/indicators', { params: { indicator_type: 'quantitative' } }).then((res) => setIndicators(res.data)).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    if (dimFilter === '全部') return indicators;
    return indicators.filter((ind) => ind.dimension === dimFilter);
  }, [indicators, dimFilter]);

  // Load single indicator comparison
  useEffect(() => {
    if (!selectedId || mode !== 'single') return;
    setLoading(true);
    apiClient.get('/comparison', { params: { indicator_id: selectedId, top_n: 20 } })
      .then((res) => { setChartData(res.data.data || []); setMeta({ unit: res.data.unit || '', name: res.data.indicator_name || '', count: res.data.count || 0, description: res.data.description || '' }); })
      .catch(() => setChartData([])).finally(() => setLoading(false));
  }, [selectedId, mode]);

  // Load matrix comparison
  async function loadMatrix() {
    if (indicatorIds.length === 0 || companyNames.length === 0) return;
    setLoading(true);
    try {
      const res = await apiClient.post('/comparison/matrix', { indicator_ids: indicatorIds, companies: companyNames });
      setMatrixData(res.data);
    } catch { setMatrixData(null); }
    finally { setLoading(false); }
  }

  const chartOption = useMemo(() => {
    if (!chartData.length) return {};
    const companies = chartData.map((d: any) => d.company).reverse();
    const values = chartData.map((d: any) => d.value).reverse();
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 140, right: 60, top: 20, bottom: 30 },
      xAxis: { type: 'value', name: meta.unit ? `${meta.name} (${meta.unit})` : meta.name, nameLocation: 'middle', nameGap: 35 },
      yAxis: { type: 'category', data: companies, axisLabel: { width: 130, overflow: 'truncate' } },
      series: [{
        type: 'bar', data: values.map((v: number, i: number) => ({
          value: v, itemStyle: { color: `rgba(67, 56, 202, ${0.3 + 0.7 * (i / Math.max(values.length - 1, 1))})`, borderRadius: [0, 4, 4, 0] },
        })),
        label: { show: true, position: 'right', formatter: (p: any) => {
          const v = p.value; if (v == null) return ''; if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(2) + 'B'; if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(2) + 'M'; if (Math.abs(v) >= 1e4) return v.toLocaleString(); if (Math.abs(v) < 0.01) return v.toFixed(4); return v.toFixed(2);
        }},
      }],
    };
  }, [chartData, meta]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">指标对比</h1>

      {/* Mode toggle */}
      <div className="flex gap-2">
        {(['single', 'matrix'] as Mode[]).map((m) => (
          <button key={m} onClick={() => setMode(m)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${mode === m ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
            {m === 'single' ? '单指标对比' : '矩阵对比'}
          </button>
        ))}
      </div>

      {mode === 'single' ? (
        <>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
            <div className="flex gap-2 mb-4">
              {(['全部', 'E', 'S', 'G'] as DimFilter[]).map((d) => (
                <button key={d} onClick={() => { setDimFilter(d); setSelectedId(''); }}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium ${dimFilter === d ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>{d === '全部' ? '全部维度' : `${d}-${d === 'E' ? '环境' : d === 'S' ? '社会' : '治理'}`}</button>
              ))}
            </div>
            <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none">
              <option value="">选择对比指标...</option>
              {filtered.map((ind) => (
                <option key={ind.id} value={ind.id}>[{ind.id}] {ind.name} {ind.unit ? `(${ind.unit})` : ''}</option>
              ))}
            </select>
            {meta.description && <p className="text-xs text-gray-400 mt-2">{meta.description}</p>}
          </div>

          {loading ? <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">加载中...</div> :
           chartData.length > 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{meta.name} — 各公司对比 ({meta.count}家公司)</h2>
              <ReactECharts option={chartOption} style={{ height: Math.max(400, 35 + chartData.length * 32) }} />
              <div className="mt-6 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-left text-xs text-gray-400 uppercase"><th className="pb-2">排名</th><th className="pb-2">公司</th><th className="pb-2">行业</th><th className="pb-2">数值</th><th className="pb-2">单位</th><th className="pb-2">置信度</th></tr></thead>
                  <tbody>
                    {chartData.map((d: any, i: number) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="py-2 text-gray-500">{i + 1}</td><td className="py-2 font-medium text-gray-900">{d.company}</td><td className="py-2 text-gray-500">{d.industry}</td>
                        <td className="py-2 font-mono text-gray-900">{d.value?.toLocaleString() ?? '-'}</td><td className="py-2 text-gray-500">{d.unit || '-'}</td>
                        <td className="py-2"><span className={`px-2 py-0.5 rounded-full text-xs ${d.confidence === 'high' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{d.confidence}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : selectedId ? <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">该指标暂无对比数据</div> :
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400"><p className="text-lg">选择指标开始对比</p></div>}
        </>
      ) : (
        /* Matrix mode */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Build basket */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
              <h3 className="font-medium text-gray-900 mb-3">对比篮</h3>
              <div className="mb-4">
                <p className="text-xs text-gray-500 mb-2">指标 ({indicatorIds.length})</p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {indicatorIds.map((id) => {
                    const ind = indicators.find((i) => i.id === id);
                    return (
                      <div key={id} className="flex items-center justify-between text-sm bg-gray-50 rounded px-2 py-1">
                        <span className="truncate flex-1 text-xs">{ind ? `[${id}] ${ind.name.slice(0,20)}` : id}</span>
                        <button onClick={() => removeIndicator(id)} className="text-red-400 hover:text-red-600 text-xs ml-2">✕</button>
                      </div>
                    );
                  })}
                </div>
                <select
                  onChange={(e) => { if (e.target.value) addIndicator(e.target.value); e.target.value = ''; }}
                  className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs mt-2">
                  <option value="">+ 添加指标</option>
                  {filtered.filter((i) => !indicatorIds.includes(i.id)).map((i) => (
                    <option key={i.id} value={i.id}>[{i.id}] {i.name.slice(0,25)}</option>
                  ))}
                </select>
              </div>
              <div>
                <p className="text-xs text-gray-500 mb-2">公司 ({companyNames.length})</p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {companyNames.map((name) => (
                    <div key={name} className="flex items-center justify-between text-sm bg-gray-50 rounded px-2 py-1">
                      <span className="text-xs truncate">{name}</span>
                      <button onClick={() => removeCompany(name)} className="text-red-400 hover:text-red-600 text-xs ml-2">✕</button>
                    </div>
                  ))}
                </div>
                <input
                  type="text" value={companySearch} onChange={(e) => setCompanySearch(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && companySearch.trim()) { addCompany(companySearch.trim()); setCompanySearch(''); } }}
                  placeholder="输入公司名按回车添加..."
                  className="w-full px-2 py-1.5 border border-gray-200 rounded text-xs mt-2" />
              </div>
              <div className="flex gap-2 mt-4">
                <button onClick={loadMatrix} disabled={indicatorIds.length === 0 || companyNames.length === 0}
                  className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-40">生成矩阵</button>
                <button onClick={clearAll} className="px-3 py-2 text-xs text-gray-400 hover:text-red-500">清空</button>
              </div>
            </div>
          </div>

          {/* Right: Matrix table */}
          <div className="lg:col-span-2">
            {matrixData ? (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 overflow-x-auto">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">指标对比矩阵</h2>
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr>
                      <th className="border border-gray-200 px-3 py-2 bg-gray-50 text-left text-xs">公司</th>
                      {matrixData.indicators.map((ind: any) => (
                        <th key={ind.id} className="border border-gray-200 px-3 py-2 bg-gray-50 text-center text-xs" title={ind.name}>
                          <div className="text-xs font-medium">[{ind.id}]</div>
                          <div className="text-[10px] text-gray-400">{ind.unit}</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {matrixData.matrix.map((row: any, ri: number) => (
                      <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                        <td className="border border-gray-200 px-3 py-2 font-medium text-xs">
                          {row.company}<br /><span className="text-gray-400">{row.industry}</span>
                        </td>
                        {matrixData.indicators.map((ind: any) => {
                          const val = row.values?.[ind.id];
                          return (
                            <td key={ind.id} className="border border-gray-200 px-3 py-2 text-center text-xs font-mono">
                              {val != null ? val.toLocaleString() : <span className="text-gray-300">-</span>}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                    {matrixData.industry_averages?.map((avg: any, ai: number) => (
                      <tr key={`avg-${ai}`} className="bg-blue-50">
                        <td className="border border-gray-200 px-3 py-2 font-medium text-xs text-blue-700">{avg.label}</td>
                        {matrixData.indicators.map((ind: any) => (
                          <td key={ind.id} className="border border-gray-200 px-3 py-2 text-center text-xs font-mono text-blue-600">
                            {avg.values?.[ind.id] != null ? avg.values[ind.id].toLocaleString() : '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button
                  onClick={() => {
                    const csv = ['公司,' + matrixData.indicators.map((i:any) => i.id).join(','),
                      ...[...matrixData.matrix, ...(matrixData.industry_averages||[])].map((r: any) =>
                        (r.company || r.label) + ',' + matrixData.indicators.map((i: any) => r.values?.[i.id] ?? '').join(',')
                      )].join('\n');
                    const blob = new Blob(['﻿' + csv], { type: 'text/csv' });
                    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'esg_comparison.csv'; a.click();
                  }}
                  className="mt-4 text-xs text-primary-600 hover:underline">导出 CSV</button>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
                <p className="text-lg">构建对比篮生成矩阵</p>
                <p className="text-sm mt-2">左侧添加指标和公司后点击"生成矩阵"</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
