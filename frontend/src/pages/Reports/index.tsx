import { useReportStore } from '../../stores/reportStore';
import StepScope from './StepScope';
import StepConfig from './StepConfig';
import StepSummary from './StepSummary';
import StepPreview from './StepPreview';

const STEPS = [
  { num: 1, label: '选择范围' },
  { num: 2, label: '配置报告' },
  { num: 3, label: '数据汇总' },
  { num: 4, label: '生成预览' },
];

function StepsBar({ current }: { current: number }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {STEPS.map((step, idx) => {
        const isDone = current > step.num;
        const isCurrent = current === step.num;
        return (
          <div key={step.num} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all ${
                  isDone
                    ? 'bg-[#52C41A] border-[#52C41A] text-white'
                    : isCurrent
                    ? 'bg-[#1677FF] border-[#1677FF] text-white'
                    : 'bg-white border-gray-300 text-gray-400'
                }`}
              >
                {isDone ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  step.num
                )}
              </div>
              <span
                className={`text-xs mt-1 font-medium ${
                  isCurrent ? 'text-[#1677FF]' : isDone ? 'text-[#52C41A]' : 'text-gray-400'
                }`}
              >
                {step.label}
              </span>
            </div>
            {idx < STEPS.length - 1 && (
              <div
                className={`w-16 sm:w-24 h-0.5 mx-2 mb-4 transition-colors ${
                  current > step.num ? 'bg-[#52C41A]' : 'bg-gray-200'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function Reports() {
  const { currentStep } = useReportStore();

  return (
    <div className="max-w-[1400px] mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">ESG报告生成器</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 sm:p-8">
        <StepsBar current={currentStep} />

        {currentStep === 1 && <StepScope />}
        {currentStep === 2 && <StepConfig />}
        {currentStep === 3 && <StepSummary />}
        {currentStep === 4 && <StepPreview />}
      </div>
    </div>
  );
}
