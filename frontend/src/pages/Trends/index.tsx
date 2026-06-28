import { useEffect, useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import type { CompanyTrend, TrendAnalysis, TrendPoint } from '../../types';
import { getTrendAnalysis, loadData } from '../../utils/dataLoader';

const DIMENSION_COLORS: Record<string, string> = {
  E: '#2e7d32',
  S: '#1565c0',
  G: '#e65100',
  ESG综合: '#4f46e5',
};

function sortPoints<T extends TrendPoint>(points: T[]) {
  return [...points].sort((a, b) => a.year.localeCompare(b.year));
}

function valueLabel(value: number | null | undefined, digits = 2) {
  if (value == null || Number.isNaN(value)) return '-';
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export default function Trends() {
  const [trendAnalysis, setTrendAnalysis] = useState<TrendAnalysis | null>(null);
  const [selectedCode, setSelectedCode] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData()
      .then((pack) => {
        const trends = getTrendAnalysis(pack) ?? null;
        setTrendAnalysis(trends);
        const first = trends?.companies.find((c) => (c.rating_years?.length ?? 0) > 1) ?? trends?.companies[0];
        if (first?.stock_code) setSelectedCode(first.stock_code);
        const firstIndustry = Object.keys(trends?.industry_trends ?? {})[0] ?? '';
        setSelectedIndustry(firstIndustry);
      })
      .finally(() => setLoading(false));
  }, []);

  const companies = trendAnalysis?.companies ?? [];
  const selectedTrend = useMemo<CompanyTrend | null>(() => {
    if (!selectedCode) return null;
    return companies.find((c) => c.stock_code === selectedCode) ?? null;
  }, [companies, selectedCode]);

  const industryNames = Object.keys(trendAnalysis?.industry_trends ?? {});
  const selectedIndustryPoints = selectedIndustry && trendAnalysis
    ? trendAnalysis.industry_trends[selectedIndustry] ?? []
    : [];

  const ratingChartOption = useMemo(() => {
    if (!selectedTrend) return {};
    const seriesKeys = ['ESG综合', 'E', 'S', 'G'];
    const yearSet = new Set<string>();
    seriesKeys.forEach((key) => (selectedTrend.esg_trend[key] ?? []).forEach((p) => yearSet.add(p.year)));
    const years = [...yearSet].sort();

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const lines = [`${params[0]?.axisValue ?? ''}`];
          params.forEach((p) => {
            const point = (selectedTrend.esg_trend[p.seriesName] ?? []).find((item) => item.year === p.axisValue);
            const rating = point?.rating ? `，评级 ${point.rating}` : '';
            lines.push(`${p.marker}${p.seriesName}: ${valueLabel(p.value)}${rating}`);
          });
          return lines.join('<br/>');
        },
      },
      legend: { data: seriesKeys, top: 0 },
      grid: { left: 54, right: 26, top: 48, bottom: 34 },
      xAxis: { type: 'category', data: years, boundaryGap: false },
      yAxis: { type: 'value', min: 0, max: 100, name: '年度均分' },
      series: seriesKeys.map((key) => ({
        name: key,
        type: 'line',
        data: years.map((year) => (selectedTrend.esg_trend[key] ?? []).find((p) => p.year === year)?.value ?? null),
        smooth: true,
        connectNulls: false,
        symbol: 'circle',
        symbolSize: key === 'ESG综合' ? 8 : 6,
        lineStyle: { width: key === 'ESG综合' ? 3 : 2 },
        color: DIMENSION_COLORS[key],
      })),
    };
  }, [selectedTrend]);

  const industryChartOption = useMemo(() => {
    const points = sortPoints(selectedIndustryPoints);
    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any[]) => {
          const p = params[0];
          const point = points.find((item) => item.year === p.axisValue);
          return `${p.axisValue}<br/>${p.marker}${selectedIndustry}: ${valueLabel(p.value)}<br/>公司数: ${point?.company_count ?? '-'}`;
        },
      },
      grid: { left: 54, right: 24, top: 24, bottom: 34 },
      xAxis: { type: 'category', data: points.map((p) => p.year), boundaryGap: false },
      yAxis: { type: 'value', min: 0, max: 100, name: '综合均分' },
      series: [{
        name: selectedIndustry,
        type: 'line',
        data: points.map((p) => p.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        areaStyle: { opacity: 0.12 },
        itemStyle: { color: '#1677FF' },
        lineStyle: { width: 3 },
      }],
    };
  }, [selectedIndustry, selectedIndustryPoints]);

  const topIndicators = useMemo(() => {
    if (!selectedTrend) return [];
    return Object.entries(selectedTrend.indicator_trends)
      .map(([name, points]) => ({ name, points: sortPoints(points).filter((p) => p.value != null) }))
      .filter((item) => item.points.length > 0)
      .sort((a, b) => b.points.length - a.points.length)
      .slice(0, 6);
  }, [selectedTrend]);

  if (loading) {
    return <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">加载趋势数据中...</div>;
  }

  if (!trendAnalysis || companies.length === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">趋势分析</h1>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          暂无趋势数据。请先运行 `python scripts/build_huazheng_trend_data.py --input 华证esg评级09.1-25.1（季度）.xlsx`，再执行 `npm run build`。
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">趋势分析</h1>
          <p className="text-sm text-gray-500 mt-1">{trendAnalysis.source} · {trendAnalysis.rating_records.toLocaleString()} 条评级观测</p>
        </div>
        <div className="text-sm text-gray-500">
          覆盖 {companies.length} 家公司 · {industryNames.length} 个行业
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">公司</label>
            <select
              value={selectedCode}
              onChange={(e) => setSelectedCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              {companies.map((company) => (
                <option key={company.stock_code ?? company.company} value={company.stock_code}>
                  {company.stock_code} · {company.company}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">行业均值</label>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
            >
              {industryNames.map((industry) => <option key={industry} value={industry}>{industry}</option>)}
            </select>
          </div>
        </div>
      </div>

      {selectedTrend && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {['ESG综合', 'E', 'S', 'G'].map((key) => {
              const points = sortPoints(selectedTrend.esg_trend[key] ?? []);
              const first = points[0];
              const last = points.at(-1);
              const delta = first && last && first.value != null && last.value != null ? last.value - first.value : null;
              return (
                <div key={key} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                  <div className="text-xs text-gray-500">{key} 趋势</div>
                  <div className="mt-2 text-2xl font-semibold text-gray-900">{valueLabel(last?.value)}</div>
                  <div className={`mt-1 text-sm ${delta == null ? 'text-gray-400' : delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {delta == null ? '暂无区间变化' : `${delta >= 0 ? '+' : ''}${valueLabel(delta)} 分`}
                  </div>
                  <div className="mt-1 text-xs text-gray-400">{first?.year ?? '-'} - {last?.year ?? '-'}</div>
                </div>
              );
            })}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">{selectedTrend.company} 华证ESG评级年度趋势</h2>
              <span className="text-xs text-gray-400">{selectedTrend.industry || '未分类'} · 年度值为季度均分</span>
            </div>
            <ReactECharts option={ratingChartOption} style={{ height: 420 }} />
          </div>

          {(selectedTrend.insights?.length ?? 0) > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">趋势洞察</h2>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                {selectedTrend.insights?.map((insight, index) => (
                  <div key={`${insight.type}-${index}`} className="border border-gray-100 rounded-lg p-3 bg-gray-50">
                    <div className="text-xs font-medium text-primary-700 mb-1">{insight.type}</div>
                    <p className="text-sm text-gray-700 leading-6">{insight.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {topIndicators.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">JSON抽取指标年度趋势</h2>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {topIndicators.map(({ name, points }) => {
                  const unit = points.find((p) => p.unit)?.unit ?? '';
                  const option = {
                    tooltip: {
                      trigger: 'axis',
                      formatter: (params: any[]) => {
                        const p = params[0];
                        return `${p.axisValue}<br/>${p.marker}${name}: ${valueLabel(p.value)} ${unit}`;
                      },
                    },
                    grid: { left: 70, right: 24, top: 24, bottom: 34 },
                    xAxis: { type: 'category', data: points.map((p) => p.year), boundaryGap: false },
                    yAxis: { type: 'value' },
                    series: [{
                      type: 'line',
                      data: points.map((p) => p.value),
                      smooth: true,
                      symbol: 'circle',
                      symbolSize: 6,
                      areaStyle: { opacity: 0.12 },
                      itemStyle: { color: '#2e7d32' },
                    }],
                  };
                  return (
                    <div key={name} className="border border-gray-100 rounded-lg p-4">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h3 className="text-sm font-medium text-gray-800">{name}</h3>
                        <span className="text-xs text-gray-400 whitespace-nowrap">{unit}</span>
                      </div>
                      <ReactECharts option={option} style={{ height: 220 }} />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}

      {selectedIndustry && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex flex-col gap-1 md:flex-row md:items-center md:justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">行业ESG综合均值趋势</h2>
            <span className="text-xs text-gray-400">{selectedIndustry}</span>
          </div>
          <ReactECharts option={industryChartOption} style={{ height: 360 }} />
        </div>
      )}
    </div>
  );
}
