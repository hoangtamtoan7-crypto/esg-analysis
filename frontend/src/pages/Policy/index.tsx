import { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../api/client';
import type { ComplianceItem } from '../../types';

export default function Policy() {
  const [items, setItems] = useState<ComplianceItem[]>([]);
  const [dimFilter, setDimFilter] = useState('');

  useEffect(() => {
    apiClient.get('/policy/compliance').then((r) => setItems(r.data)).catch(() => {});
  }, []);

  const filtered = useMemo(() => {
    if (!dimFilter) return items;
    return items.filter((i) => i.dimension === dimFilter);
  }, [items, dimFilter]);

  // Disclosure rate bar chart
  const barOption = useMemo(() => {
    const data = [...filtered].sort((a, b) => a.disclosure_rate - b.disclosure_rate);
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 160, right: 50, top: 10, bottom: 20 },
      xAxis: { type: 'value', name: '披露率', max: 1, axisLabel: { formatter: (v: number) => (v * 100).toFixed(0) + '%' } },
      yAxis: { type: 'category', data: data.map((i) => `[${i.indicator_id}] ${i.indicator_name}`.slice(0, 30)), axisLabel: { fontSize: 10 } },
      series: [{
        type: 'bar',
        data: data.map((i) => ({
          value: i.disclosure_rate,
          itemStyle: {
            color: i.disclosure_rate > 0.7 ? '#22c55e' : i.disclosure_rate > 0.4 ? '#f59e0b' : '#ef4444',
            borderRadius: [0, 3, 3, 0],
          },
        })),
        label: { show: true, position: 'right', formatter: (p: any) => (p.value * 100).toFixed(0) + '%', fontSize: 10 },
      }],
    };
  }, [filtered]);

  // Dimension summary
  const dimSummary = useMemo(() => {
    const map: Record<string, { count: number; total_rate: number }> = {};
    items.forEach((i) => {
      if (!map[i.dimension]) map[i.dimension] = { count: 0, total_rate: 0 };
      map[i.dimension].count++;
      map[i.dimension].total_rate += i.disclosure_rate;
    });
    return Object.entries(map).map(([dim, v]) => ({
      dim,
      label: dim === 'E' ? '环境' : dim === 'S' ? '社会' : '治理',
      avg_rate: Math.round((v.total_rate / v.count) * 100),
      count: v.count,
    }));
  }, [items]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">披露合规分析</h1>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {dimSummary.map((d) => (
          <div key={d.dim} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 text-center">
            <div className={`text-3xl font-bold ${
              d.dim === 'E' ? 'text-green-600' : d.dim === 'S' ? 'text-blue-600' : 'text-orange-600'
            }`}>{d.avg_rate}%</div>
            <div className="text-sm text-gray-500 mt-1">{d.label}维度平均披露率</div>
            <div className="text-xs text-gray-400 mt-0.5">{d.count}个指标</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="flex gap-3">
          {['', 'E', 'S', 'G'].map((d) => (
            <button
              key={d}
              onClick={() => setDimFilter(d)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                dimFilter === d ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {d === '' ? '全部维度' : `${d}维度`}
            </button>
          ))}
        </div>
      </div>

      {/* Disclosure chart */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">各指标披露率 (共{items.length}个指标)</h2>
        <ReactECharts option={barOption} style={{ height: Math.max(500, filtered.length * 28) }} />
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">披露率明细</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-gray-400 uppercase">
                <th className="pb-2">指标ID</th>
                <th className="pb-2">名称</th>
                <th className="pb-2">维度</th>
                <th className="pb-2">类型</th>
                <th className="pb-2">披露率</th>
                <th className="pb-2">披露行业详情</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.indicator_id} className="border-b border-gray-50">
                  <td className="py-2 font-mono text-xs text-gray-500">{item.indicator_id}</td>
                  <td className="py-2 text-gray-900">{item.indicator_name}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      item.dimension === 'E' ? 'bg-green-100 text-green-700' :
                      item.dimension === 'S' ? 'bg-blue-100 text-blue-700' :
                      'bg-orange-100 text-orange-700'
                    }`}>{item.dimension}</span>
                  </td>
                  <td className="py-2 text-xs text-gray-500">{item.indicator_type === 'quantitative' ? '定量' : '定性'}</td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${item.disclosure_rate > 0.7 ? 'bg-green-500' : item.disclosure_rate > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                          style={{ width: `${item.disclosure_rate * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-mono">{Math.round(item.disclosure_rate * 100)}%</span>
                    </div>
                  </td>
                  <td className="py-2 text-xs text-gray-400">
                    {item.industry_breakdown.slice(0, 3).map((ind) => (
                      <span key={ind.industry} className="mr-2">{ind.industry} {Math.round(ind.disclosure_rate * 100)}%</span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
