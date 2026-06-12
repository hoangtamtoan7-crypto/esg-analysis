import { useState } from 'react';
import { useReportStore } from '../../stores/reportStore';
import type { ReportTemplate, ReportDimension } from '../../stores/reportStore';

const TEMPLATES: { value: ReportTemplate; icon: string; title: string; desc: string }[] = [
  {
    value: 'standard',
    icon: '📋',
    title: '标准摘要',
    desc: 'E+S+G 评分 + 关键指标摘要，适合快速概览',
  },
  {
    value: 'detailed',
    icon: '📊',
    title: '完整报告',
    desc: '全部 52 个指标 + 全维度深度分析',
  },
  {
    value: 'investment',
    icon: '🎯',
    title: '投资分析',
    desc: 'ESG 评分 + 风险提示 + 行业对比，适合投资决策',
  },
];

const DIMENSIONS: { value: ReportDimension; label: string; color: string; indicators: string[] }[] = [
  {
    value: 'E',
    label: '环境 (Environmental)',
    color: '#52C41A',
    indicators: ['碳排放总量', '可再生能源比例', '能源消耗强度', '废水排放量', '绿色产品收入', '环境违规次数'],
  },
  {
    value: 'S',
    label: '社会 (Social)',
    color: '#1677FF',
    indicators: ['员工总数', '女性员工占比', '员工培训时长', '安全事故次数', '社会公益支出', '供应链管理'],
  },
  {
    value: 'G',
    label: '治理 (Governance)',
    color: '#FA8C16',
    indicators: ['独立董事占比', '高管薪酬披露', '反腐政策', '信息披露质量', '董事会多元化', '股东权益保护'],
  },
];

export default function StepConfig() {
  const {
    reportTitle, setReportTitle,
    reportTemplate, setReportTemplate,
    selectedDimensions, toggleDimension,
    author, setAuthor,
    reportDate, setReportDate,
    setCurrentStep,
    selectedYears,
  } = useReportStore();

  const [expandedDims, setExpandedDims] = useState<ReportDimension[]>([]);
  const [titleError, setTitleError] = useState('');

  function toggleExpand(dim: ReportDimension) {
    setExpandedDims((prev) =>
      prev.includes(dim) ? prev.filter((d) => d !== dim) : [...prev, dim]
    );
  }

  function handleTitle(v: string) {
    setReportTitle(v);
    if (!v.trim()) {
      setTitleError('报告标题不能为空');
    } else {
      setTitleError('');
    }
  }

  const canNext = reportTitle.trim().length > 0 && selectedDimensions.length > 0;

  const defaultTitle = `${selectedYears[0] ?? new Date().getFullYear()}年度ESG评估报告`;

  return (
    <div className="space-y-6">
      {/* 报告标题 */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-2">报告标题</h3>
        <input
          type="text"
          value={reportTitle || defaultTitle}
          onChange={(e) => handleTitle(e.target.value)}
          placeholder={defaultTitle}
          className={`w-full px-4 py-2.5 border rounded-xl text-sm outline-none focus:ring-2 focus:ring-[#1677FF] transition-colors ${
            titleError ? 'border-[#FF4D4F] focus:ring-[#FF4D4F]' : 'border-gray-200'
          }`}
        />
        {titleError && <p className="text-xs text-[#FF4D4F] mt-1">{titleError}</p>}
      </div>

      {/* 报告模板 */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">报告模板</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {TEMPLATES.map((tpl) => (
            <button
              key={tpl.value}
              onClick={() => setReportTemplate(tpl.value)}
              className={`p-4 rounded-xl border-2 text-left transition-all cursor-pointer ${
                reportTemplate === tpl.value
                  ? 'border-[#1677FF] bg-[#1677FF]/5'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <div className="text-2xl mb-2">{tpl.icon}</div>
              <div className="font-semibold text-gray-800 text-sm">{tpl.title}</div>
              <div className="text-xs text-gray-500 mt-1 leading-relaxed">{tpl.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* 指标维度 */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">指标维度</h3>
        <div className="space-y-2">
          {DIMENSIONS.map((dim) => {
            const isSelected = selectedDimensions.includes(dim.value);
            const isExpanded = expandedDims.includes(dim.value);
            return (
              <div key={dim.value} className="border border-gray-200 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 bg-white">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleDimension(dim.value)}
                    className="accent-[#1677FF]"
                    id={`dim-${dim.value}`}
                  />
                  <label
                    htmlFor={`dim-${dim.value}`}
                    className="flex-1 text-sm font-medium text-gray-800 cursor-pointer"
                    style={{ color: isSelected ? dim.color : undefined }}
                  >
                    {dim.label}
                  </label>
                  <button
                    onClick={() => toggleExpand(dim.value)}
                    className="text-xs text-gray-400 hover:text-gray-600 cursor-pointer transition-colors"
                  >
                    {isExpanded ? '收起' : '展开指标'} {isExpanded ? '▲' : '▼'}
                  </button>
                </div>
                {isExpanded && (
                  <div className="px-4 pb-3 bg-gray-50 flex flex-wrap gap-1.5">
                    {dim.indicators.map((ind) => (
                      <span
                        key={ind}
                        className="text-xs px-2 py-1 rounded-full bg-white border border-gray-200 text-gray-600"
                      >
                        {ind}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {selectedDimensions.length === 0 && (
          <p className="text-xs text-[#FF4D4F] mt-1">请至少选择一个维度</p>
        )}
      </div>

      {/* 编制信息 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">编制人</h3>
          <input
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="请输入编制人姓名"
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-[#1677FF]"
          />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">编制日期</h3>
          <input
            type="date"
            value={reportDate}
            onChange={(e) => setReportDate(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-[#1677FF] cursor-pointer"
          />
        </div>
      </div>

      {/* 底部按钮 */}
      <div className="flex justify-between pt-4 border-t border-gray-100">
        <button
          onClick={() => setCurrentStep(1)}
          className="px-5 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          上一步
        </button>
        <button
          onClick={() => setCurrentStep(3)}
          disabled={!canNext}
          className="px-6 py-2 bg-[#1677FF] text-white rounded-lg text-sm font-medium hover:bg-[#0958d9] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
        >
          下一步
        </button>
      </div>
    </div>
  );
}
