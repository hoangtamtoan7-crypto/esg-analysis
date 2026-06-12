import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../api/client';
import { useComparisonBasket } from '../../stores/comparisonStore';
import type { Indicator, FilterMetadata } from '../../types';

export default function Indicators() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [meta, setMeta] = useState<FilterMetadata | null>(null);
  const [filters, setFilters] = useState({ dimension: '', indicator_type: '', keyword: '' });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [indicatorData, setIndicatorData] = useState<any>(null);
  const { indicatorIds, addIndicator, removeIndicator } = useComparisonBasket();
  const navigate = useNavigate();

  useEffect(() => {
    apiClient.get('/indicators/filters/metadata').then((r) => setMeta(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    const params: any = {};
    if (filters.dimension) params.dimension = filters.dimension;
    if (filters.indicator_type) params.indicator_type = filters.indicator_type;
    if (filters.keyword) params.keyword = filters.keyword;
    apiClient.get('/indicators', { params }).then((r) => setIndicators(r.data)).catch(() => {});
  }, [filters]);

  async function showDetail(id: string) {
    setSelectedId(id);
    try {
      const res = await apiClient.get(`/indicators/${id}`);
      setIndicatorData(res.data);
    } catch { setIndicatorData(null); }
  }

  const hasBasket = indicatorIds.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">指标浏览器</h1>
        {hasBasket && (
          <button
            onClick={() => navigate('/comparison')}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            对比篮 ({indicatorIds.length}) → 开始对比
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex flex-wrap gap-3">
          <select
            value={filters.dimension}
            onChange={(e) => setFilters({ ...filters, dimension: e.target.value })}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          >
            <option value="">全部维度</option>
            <option value="E">E - 环境</option>
            <option value="S">S - 社会</option>
            <option value="G">G - 治理</option>
          </select>
          <select
            value={filters.indicator_type}
            onChange={(e) => setFilters({ ...filters, indicator_type: e.target.value })}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
          >
            <option value="">全部类型</option>
            <option value="quantitative">定量指标</option>
            <option value="qualitative">定性指标</option>
          </select>
          <input
            type="text"
            value={filters.keyword}
            onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
            placeholder="搜索指标..."
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm flex-1 min-w-[200px]"
          />
        </div>
        {meta && (
          <p className="text-xs text-gray-400 mt-3">
            共 {meta.total_indicators} 个指标 · 覆盖 {meta.total_companies} 家公司 · {meta.industries.length} 个行业
          </p>
        )}
      </div>

      {/* Indicator grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indicators.map((ind) => (
          <div
            key={ind.id}
            onClick={() => showDetail(ind.id)}
            className={`bg-white rounded-xl shadow-sm border p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedId === ind.id ? 'ring-2 ring-primary-500' :
              indicatorIds.includes(ind.id) ? 'ring-1 ring-primary-300 bg-primary-50' : 'border-gray-100'
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    ind.dimension === 'E' ? 'bg-green-100 text-green-700' :
                    ind.dimension === 'S' ? 'bg-blue-100 text-blue-700' :
                    'bg-orange-100 text-orange-700'
                  }`}>{ind.dimension}</span>
                  <span className="text-xs text-gray-400">{ind.indicator_type === 'quantitative' ? '定量' : '定性'}</span>
                </div>
                <h3 className="font-medium text-gray-900 text-sm">{ind.name}</h3>
                <p className="text-xs text-gray-400 mt-1">
                  [{ind.id}] {ind.unit ? `· ${ind.unit}` : ''}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  indicatorIds.includes(ind.id) ? removeIndicator(ind.id) : addIndicator(ind.id);
                }}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  indicatorIds.includes(ind.id)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-primary-100 hover:text-primary-700'
                }`}
              >
                {indicatorIds.includes(ind.id) ? '已选' : '+对比'}
              </button>
            </div>
            {ind.description && (
              <p className="text-xs text-gray-500 mt-2 line-clamp-2">{ind.description}</p>
            )}
          </div>
        ))}
      </div>

      {/* Indicator detail modal-like section */}
      {selectedId && indicatorData && (
        <div className="bg-white rounded-xl shadow-sm border border-primary-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                [{indicatorData.indicator.id}] {indicatorData.indicator.name}
              </h2>
              <p className="text-sm text-gray-500">{indicatorData.indicator.description}</p>
            </div>
            <button onClick={() => setSelectedId(null)} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>

          {indicatorData.values.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs text-gray-400 uppercase">
                      <th className="pb-2">公司</th><th className="pb-2">行业</th><th className="pb-2">数值</th>
                    </tr>
                  </thead>
                  <tbody>
                    {indicatorData.values.slice(0, 15).map((v: any, i: number) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="py-1.5 text-gray-900">{v.company}</td>
                        <td className="py-1.5 text-gray-500 text-xs">{v.industry}</td>
                        <td className="py-1.5 font-mono text-gray-800">{v.value?.toLocaleString() ?? '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p className="text-xs text-gray-400 mt-2">共 {indicatorData.company_count} 家公司有数据</p>
              </div>
              <div className="lg:col-span-2">
                {(() => {
                  const data = [...indicatorData.values].reverse();
                  const opt = {
                    tooltip: { trigger: 'axis' },
                    grid: { left: 130, right: 50, top: 10, bottom: 20 },
                    xAxis: { type: 'value' },
                    yAxis: { type: 'category', data: data.map((d: any) => d.company), axisLabel: { width: 120, overflow: 'truncate' } },
                    series: [{
                      type: 'bar', data: data.map((d: any, i: number) => ({
                        value: d.value,
                        itemStyle: { color: `rgba(67,56,202,${0.3 + 0.7 * i / data.length})`, borderRadius: [0, 3, 3, 0] },
                      })),
                      label: { show: true, position: 'right', fontSize: 10 },
                    }],
                  };
                  return <ReactECharts option={opt} style={{ height: Math.max(300, indicatorData.values.length * 22) }} />;
                })()}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
