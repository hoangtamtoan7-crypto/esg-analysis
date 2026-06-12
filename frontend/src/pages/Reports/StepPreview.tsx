import { useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { useReportStore } from '../../stores/reportStore';

interface CompanyData {
  name: string;
  esg_scores?: {
    esg_composite: number;
    e_score: number;
    s_score: number;
    g_score: number;
  };
  quantitative_indicators?: { indicator_id: string; indicator_name: string; value: number | null; unit: string }[];
}

function getScoreChartOption(companies: CompanyData[]) {
  const names = companies.map((c) => c.name);
  const scores = companies.map((c) => +(c.esg_scores?.esg_composite ?? 0).toFixed(3));
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 120, right: 30, top: 20, bottom: 20 },
    xAxis: { type: 'value', max: 1, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: scores,
      itemStyle: { color: '#1677FF', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 11 },
    }],
  };
}

function getDimChartOption(companies: CompanyData[]) {
  return {
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    grid: { left: 100, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'value', max: 1 },
    yAxis: { type: 'category', data: companies.map((c) => c.name) },
    series: [
      {
        name: 'E（环境）',
        type: 'bar',
        data: companies.map((c) => +(c.esg_scores?.e_score ?? 0).toFixed(3)),
        itemStyle: { color: '#52C41A' },
      },
      {
        name: 'S（社会）',
        type: 'bar',
        data: companies.map((c) => +(c.esg_scores?.s_score ?? 0).toFixed(3)),
        itemStyle: { color: '#1677FF' },
      },
      {
        name: 'G（治理）',
        type: 'bar',
        data: companies.map((c) => +(c.esg_scores?.g_score ?? 0).toFixed(3)),
        itemStyle: { color: '#FA8C16' },
      },
    ],
  };
}

export default function StepPreview() {
  const {
    reportTitle, author, reportDate,
    selectedCompanies, selectedYears,
    reportData, setCurrentStep, reset,
  } = useReportStore();

  const printRef = useRef<HTMLDivElement>(null);

  const companyDetails: CompanyData[] = (reportData?.companyDetails as CompanyData[]) ?? [];

  // 前10个关键指标（取第一家公司）
  const keyIndicators = companyDetails[0]?.quantitative_indicators
    ?.filter((i) => i.value != null)
    .slice(0, 10) ?? [];

  function handlePrint() {
    window.print();
  }

  function handleCopyLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
      alert('链接已复制到剪贴板');
    }).catch(() => {
      prompt('复制以下链接：', url);
    });
  }

  const hasCompanies = companyDetails.length > 0;

  return (
    <div className="space-y-4">
      {/* 操作按钮 */}
      <div className="no-print flex flex-wrap gap-3 justify-end">
        <button
          onClick={() => { reset(); }}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          重新生成
        </button>
        <button
          onClick={handleCopyLink}
          className="px-4 py-2 border border-[#1677FF] text-[#1677FF] rounded-lg text-sm hover:bg-[#1677FF]/5 cursor-pointer transition-colors"
        >
          复制分享链接
        </button>
        <button
          onClick={handlePrint}
          className="px-5 py-2 bg-[#1677FF] text-white rounded-lg text-sm font-medium hover:bg-[#0958d9] cursor-pointer transition-colors"
        >
          下载 PDF
        </button>
      </div>

      {/* A4 报告预览区 */}
      <div
        ref={printRef}
        className="bg-white rounded-xl shadow-sm border border-gray-200 mx-auto p-8 space-y-8"
        style={{ maxWidth: 800 }}
      >
        {/* 标题页 */}
        <div className="text-center border-b border-gray-200 pb-8">
          <div className="inline-block bg-[#1677FF]/10 text-[#1677FF] text-xs font-medium px-3 py-1 rounded-full mb-4">
            ESG数据智能平台
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{reportTitle}</h1>
          <div className="text-sm text-gray-500 space-y-1">
            {selectedCompanies.length > 0 && (
              <p>研究对象：{selectedCompanies.join('、')}</p>
            )}
            <p>报告年份：{selectedYears.join('、')}</p>
            {author && <p>编制人：{author}</p>}
            <p>编制日期：{reportDate}</p>
          </div>
        </div>

        {/* ESG 综合评分 */}
        {hasCompanies && (
          <div>
            <h2 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="w-1 h-4 rounded-full bg-[#1677FF] inline-block" />
              ESG综合评分排名
            </h2>
            <ReactECharts
              option={getScoreChartOption(companyDetails)}
              style={{ height: Math.max(120, companyDetails.length * 48) }}
            />
          </div>
        )}

        {/* E/S/G 维度对比 */}
        {hasCompanies && (
          <div>
            <h2 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="w-1 h-4 rounded-full bg-[#52C41A] inline-block" />
              E/S/G 维度得分对比
            </h2>
            <ReactECharts
              option={getDimChartOption(companyDetails)}
              style={{ height: Math.max(160, companyDetails.length * 60) }}
            />
          </div>
        )}

        {/* 关键指标表格 */}
        {keyIndicators.length > 0 && (
          <div>
            <h2 className="text-base font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="w-1 h-4 rounded-full bg-[#FA8C16] inline-block" />
              关键指标（{companyDetails[0]?.name}）
            </h2>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-gray-50">
                  <th className="text-left px-3 py-2 text-xs text-gray-500 font-medium border border-gray-200">指标名称</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 font-medium border border-gray-200">数值</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 font-medium border border-gray-200">单位</th>
                  <th className="text-left px-3 py-2 text-xs text-gray-500 font-medium border border-gray-200">维度</th>
                </tr>
              </thead>
              <tbody>
                {keyIndicators.map((ind, i) => (
                  <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-3 py-2 border border-gray-200 text-gray-800">{ind.indicator_name}</td>
                    <td className="px-3 py-2 border border-gray-200 font-mono text-gray-900">
                      {ind.value != null ? ind.value.toLocaleString() : '-'}
                    </td>
                    <td className="px-3 py-2 border border-gray-200 text-gray-500">{ind.unit || '-'}</td>
                    <td className="px-3 py-2 border border-gray-200">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        ind.indicator_id.startsWith('E') ? 'bg-green-100 text-[#52C41A]' :
                        ind.indicator_id.startsWith('S') ? 'bg-blue-100 text-[#1677FF]' :
                        'bg-orange-100 text-[#FA8C16]'
                      }`}>
                        {ind.indicator_id[0]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* 无后端数据时的占位提示 */}
        {!hasCompanies && (
          <div className="text-center py-12 text-gray-400">
            <div className="text-4xl mb-3">📋</div>
            <p className="text-base font-medium mb-1">报告已生成</p>
            <p className="text-sm">连接后端服务后可获取完整图表数据</p>
            <div className="mt-4 grid grid-cols-3 gap-3 max-w-xs mx-auto">
              {selectedCompanies.map((name) => (
                <div key={name} className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-xs font-medium text-gray-700 truncate">{name}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 页脚 */}
        <div className="border-t border-gray-200 pt-4 text-center text-xs text-gray-400">
          本报告由 ESG数据智能平台 自动生成 · 数据来源：上市公司ESG报告
        </div>
      </div>

      {/* 返回按钮 */}
      <div className="no-print flex justify-start">
        <button
          onClick={() => setCurrentStep(3)}
          className="px-5 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50 cursor-pointer transition-colors"
        >
          上一步
        </button>
      </div>
    </div>
  );
}
