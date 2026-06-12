import { useEffect } from 'react';
import { useAppStore } from '../../stores/appStore';
import apiClient from '../../api/client';
import type { OverviewData } from '../../types';

// Sparkline SVG 迷你趋势图（模拟数据）
function Sparkline({ color }: { color: string }) {
  const points = [30, 45, 35, 60, 50, 70, 65, 80];
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;
  const w = 80, h = 32;
  const xs = points.map((_, i) => (i / (points.length - 1)) * w);
  const ys = points.map((v) => h - ((v - min) / range) * h);
  const d = xs.map((x, i) => `${i === 0 ? 'M' : 'L'} ${x},${ys[i]}`).join(' ');
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none">
      <path d={d} stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ESG 评分热力图（行业矩阵）
function ESGHeatmap({ distribution }: { distribution: { industry: string; count: number }[] }) {
  const mockScores: Record<string, number> = {
    '制造业': 0.72, '金融业': 0.68, '科技业': 0.75, '能源业': 0.58,
    '消费品': 0.65, '医疗健康': 0.70, '房地产': 0.55, '交通运输': 0.62,
  };
  const items = distribution.slice(0, 8).map((d) => ({
    industry: d.industry,
    score: mockScores[d.industry] ?? (0.5 + Math.random() * 0.3),
  }));

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {items.map((item) => {
        const pct = Math.round(item.score * 100);
        const bg = item.score >= 0.7 ? '#52C41A' : item.score >= 0.6 ? '#1677FF' : '#FA8C16';
        const opacity = 0.15 + item.score * 0.7;
        return (
          <div
            key={item.industry}
            className="rounded-lg p-3 text-center"
            style={{ backgroundColor: bg + Math.round(opacity * 255).toString(16).padStart(2, '0') }}
          >
            <div className="text-sm font-bold" style={{ color: bg }}>{pct}</div>
            <div className="text-xs text-gray-600 mt-0.5 truncate">{item.industry}</div>
          </div>
        );
      })}
    </div>
  );
}

const kpiDefs = [
  { label: '覆盖公司', key: 'companies' as const, color: '#1677FF', suffix: '家' },
  { label: '已处理报告', key: 'reports' as const, color: '#52C41A', suffix: '份' },
  { label: '定量指标', key: 'quantitative_indicators' as const, color: '#FA8C16', suffix: '项' },
  { label: '覆盖行业', key: 'industries' as const, color: '#722ED1', suffix: '个' },
];

export default function Home() {
  const { overview, setOverview } = useAppStore();

  useEffect(() => {
    apiClient.get<OverviewData>('/overview').then((res) => setOverview(res.data)).catch(console.error);
  }, [setOverview]);

  if (!overview) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-56 bg-gray-200 rounded animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl p-5 h-28 animate-pulse" />
          ))}
        </div>
        <div className="bg-white rounded-xl h-48 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-[1400px] mx-auto">
      <h1 className="text-2xl font-bold text-gray-900">ESG数据智能平台</h1>

      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {kpiDefs.map((kpi) => (
          <div
            key={kpi.key}
            className="bg-white rounded-xl shadow-sm p-5 flex flex-col justify-between transition-all duration-200 hover:-translate-y-1 hover:shadow-md cursor-pointer"
          >
            <div>
              <div className="text-sm text-[#8c8c8c] mb-1">{kpi.label}</div>
              <div className="text-[28px] font-bold" style={{ color: kpi.color }}>
                {overview[kpi.key].toLocaleString()}
                <span className="text-base font-normal text-gray-400 ml-1">{kpi.suffix}</span>
              </div>
            </div>
            <div className="mt-2 flex justify-end">
              <Sparkline color={kpi.color} />
            </div>
          </div>
        ))}
      </div>

      {/* 行业分布 + 热力图 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">行业覆盖分布</h2>
          <div className="grid grid-cols-2 gap-2">
            {overview.industry_distribution.map((item) => (
              <div
                key={item.industry}
                className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg"
              >
                <span className="text-sm text-gray-700 truncate">{item.industry}</span>
                <span className="text-sm font-semibold text-[#1677FF] ml-2 flex-shrink-0">{item.count} 家</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4">ESG评分分布热力图</h2>
          <ESGHeatmap distribution={overview.industry_distribution} />
          <div className="mt-3 flex items-center gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-3 rounded-sm bg-[#52C41A] opacity-70" />
              优秀 ≥70
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-3 rounded-sm bg-[#1677FF] opacity-70" />
              良好 60-70
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-3 rounded-sm bg-[#FA8C16] opacity-70" />
              待提升 &lt;60
            </span>
          </div>
        </div>
      </div>

      {/* 平台说明 */}
      <div className="bg-gradient-to-r from-[#1677FF] to-[#0958d9] rounded-xl p-6 text-white">
        <h2 className="text-lg font-bold mb-1">ESG数据智能提取与分析系统</h2>
        <p className="text-white/80 text-sm">
          基于DeepSeek大模型，自动提取A股上市公司ESG报告中的52项关键指标，支持多公司横向对比与行业趋势分析。
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          {[
            { label: '数据质量均分', value: overview.avg_quality_score?.toFixed(3) ?? '-' },
            { label: '定量指标', value: overview.quantitative_indicators },
            { label: '定性指标', value: overview.qualitative_indicators },
          ].map((s) => (
            <div key={s.label} className="bg-white/10 rounded-lg px-4 py-2 text-center">
              <div className="text-xl font-bold">{s.value}</div>
              <div className="text-xs text-white/70 mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
