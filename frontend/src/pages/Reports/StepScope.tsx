import { useState, useEffect, useCallback } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useReportStore } from '../../stores/reportStore';
import type { ReportType } from '../../stores/reportStore';
import apiClient from '../../api/client';

const YEARS = ['2022', '2023', '2024', '2025'];

const TYPE_CARDS: { value: ReportType; title: string; desc: string; icon: string }[] = [
  { value: 'single', title: '单公司报告', desc: '深度分析单家公司ESG表现', icon: '🏢' },
  { value: 'multi', title: '多公司对比', desc: '横向对比多家公司ESG指标', icon: '📊' },
  { value: 'industry', title: '行业对比', desc: '查看同行业公司ESG基准', icon: '🏭' },
];

const INDUSTRIES = [
  '制造业', '金融业', '科技业', '能源业', '消费品',
  '医疗健康', '房地产', '交通运输', '公用事业', '农林牧渔',
];

interface SearchResult {
  name: string;
  industry?: string;
  report_year?: string;
  quality_score?: number;
  coverage?: number;
}

export default function StepScope() {
  const {
    reportType, setReportType,
    selectedCompanies, toggleCompany,
    selectedIndustry, setSelectedIndustry,
    selectedYears, toggleYear,
    setCurrentStep,
  } = useReportStore();

  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 1) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const res = await apiClient.get('/companies/search', { params: { q } });
      setSearchResults(res.data);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => doSearch(search), 300);
    return () => clearTimeout(t);
  }, [search, doSearch]);

  const canNext =
    reportType === 'industry'
      ? selectedIndustry.length > 0 && selectedYears.length > 0
      : selectedCompanies.length > 0 && selectedYears.length > 0;

  return (
    <div className="space-y-6">
      {/* 报告类型 */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">选择报告类型</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {TYPE_CARDS.map((card) => (
            <button
              key={card.value}
              onClick={() => setReportType(card.value)}
              className={`p-4 rounded-xl border-2 text-left transition-all cursor-pointer ${
                reportType === card.value
                  ? 'border-[#1677FF] bg-[#1677FF]/5'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="text-2xl mb-2">{card.icon}</div>
              <div className="font-semibold text-gray-800 text-sm">{card.title}</div>
              <div className="text-xs text-gray-500 mt-1">{card.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 公司选择（非行业模式） */}
      {reportType !== 'industry' && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            选择公司
            {reportType === 'single' && <span className="text-gray-400 font-normal ml-1">（最多1家）</span>}
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 搜索区 */}
            <div className="space-y-2">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="搜索公司名称..."
                  className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-[#1677FF] outline-none"
                />
                {searching && <span className="absolute right-3 top-3 text-xs text-gray-400">搜索中...</span>}
              </div>
              <div className="border border-gray-200 rounded-xl overflow-hidden max-h-60 overflow-y-auto">
                {searchResults.length === 0 && search.length === 0 && (
                  <div className="py-8 text-center text-sm text-gray-400">输入公司名称开始搜索</div>
                )}
                {searchResults.length === 0 && search.length > 0 && !searching && (
                  <div className="py-8 text-center text-sm text-gray-400">未找到相关公司</div>
                )}
                {searchResults.map((r) => {
                  const isSelected = selectedCompanies.includes(r.name);
                  const disabledSingle = reportType === 'single' && !isSelected && selectedCompanies.length >= 1;
                  return (
                    <label
                      key={r.name}
                      className={`flex items-start gap-3 px-4 py-3 border-b border-gray-50 last:border-0 transition-colors ${
                        disabledSingle ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:bg-[#1677FF]/5'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isSelected}
                        disabled={disabledSingle}
                        onChange={() => !disabledSingle && toggleCompany(r.name)}
                        className="mt-0.5 accent-[#1677FF]"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-800 text-sm">{r.name}</div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          {r.industry && <span className="bg-gray-100 rounded px-1.5 py-0.5 mr-1">{r.industry}</span>}
                          {r.report_year}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* 已选公司 */}
            <div>
              <div className="border border-gray-200 rounded-xl p-3 min-h-32 bg-gray-50">
                <div className="text-xs text-gray-400 mb-2">
                  已选 {selectedCompanies.length} 家公司
                </div>
                {selectedCompanies.length === 0 ? (
                  <div className="text-center text-sm text-gray-300 py-6">暂未选择公司</div>
                ) : (
                  <div className="space-y-1.5">
                    {selectedCompanies.map((name) => (
                      <div
                        key={name}
                        className="flex items-center justify-between bg-white rounded-lg px-3 py-2 border border-gray-100"
                      >
                        <span className="text-sm text-gray-800">{name}</span>
                        <button
                          onClick={() => toggleCompany(name)}
                          className="text-gray-400 hover:text-red-500 cursor-pointer transition-colors"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 行业选择（行业模式） */}
      {reportType === 'industry' && (
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">选择行业</h3>
          <select
            value={selectedIndustry}
            onChange={(e) => setSelectedIndustry(e.target.value)}
            className="w-full max-w-sm border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:ring-2 focus:ring-[#1677FF] outline-none cursor-pointer"
          >
            <option value="">请选择行业...</option>
            {INDUSTRIES.map((ind) => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>
      )}

      {/* 年份选择 */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">选择年份</h3>
        <div className="flex flex-wrap gap-2">
          {YEARS.map((year) => (
            <button
              key={year}
              onClick={() => toggleYear(year)}
              className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all cursor-pointer ${
                selectedYears.includes(year)
                  ? 'bg-[#1677FF] text-white border-[#1677FF]'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-[#1677FF]'
              }`}
            >
              {year}
            </button>
          ))}
        </div>
      </div>

      {/* 底部按钮 */}
      <div className="flex justify-between pt-4 border-t border-gray-100">
        <button
          onClick={() => useReportStore.getState().reset()}
          className="px-5 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          重置
        </button>
        <button
          onClick={() => setCurrentStep(2)}
          disabled={!canNext}
          className="px-6 py-2 bg-[#1677FF] text-white rounded-lg text-sm font-medium hover:bg-[#0958d9] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
        >
          下一步
        </button>
      </div>
    </div>
  );
}
