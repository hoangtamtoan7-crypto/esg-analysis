import { create } from 'zustand';

export type ReportType = 'single' | 'industry' | 'multi';
export type ReportTemplate = 'standard' | 'detailed' | 'investment';
export type ReportDimension = 'E' | 'S' | 'G';

interface ReportState {
  currentStep: number;
  setCurrentStep: (step: number) => void;

  reportType: ReportType;
  setReportType: (type: ReportType) => void;
  selectedCompanies: string[];
  toggleCompany: (name: string) => void;
  selectedIndustry: string;
  setSelectedIndustry: (industry: string) => void;
  selectedYears: string[];
  toggleYear: (year: string) => void;

  reportTitle: string;
  setReportTitle: (title: string) => void;
  reportTemplate: ReportTemplate;
  setReportTemplate: (template: ReportTemplate) => void;
  selectedDimensions: ReportDimension[];
  toggleDimension: (dim: ReportDimension) => void;
  author: string;
  setAuthor: (author: string) => void;
  reportDate: string;
  setReportDate: (date: string) => void;

  reportData: Record<string, unknown> | null;
  setReportData: (data: Record<string, unknown>) => void;
  reportLoading: boolean;
  setReportLoading: (loading: boolean) => void;

  reset: () => void;
}

const today = new Date().toISOString().slice(0, 10);

const initialState = {
  currentStep: 1,
  reportType: 'single' as ReportType,
  selectedCompanies: [] as string[],
  selectedIndustry: '',
  selectedYears: [String(new Date().getFullYear())],
  reportTitle: `${new Date().getFullYear()}年度ESG评估报告`,
  reportTemplate: 'standard' as ReportTemplate,
  selectedDimensions: ['E', 'S', 'G'] as ReportDimension[],
  author: '',
  reportDate: today,
  reportData: null,
  reportLoading: false,
};

export const useReportStore = create<ReportState>((set, get) => ({
  ...initialState,

  setCurrentStep: (step) => set({ currentStep: step }),

  setReportType: (reportType) => set({ reportType, selectedCompanies: [], selectedIndustry: '' }),

  toggleCompany: (name) => {
    const { selectedCompanies } = get();
    set({
      selectedCompanies: selectedCompanies.includes(name)
        ? selectedCompanies.filter((c) => c !== name)
        : [...selectedCompanies, name],
    });
  },

  setSelectedIndustry: (selectedIndustry) => set({ selectedIndustry }),

  toggleYear: (year) => {
    const { selectedYears } = get();
    set({
      selectedYears: selectedYears.includes(year)
        ? selectedYears.filter((y) => y !== year)
        : [...selectedYears, year],
    });
  },

  setReportTitle: (reportTitle) => set({ reportTitle }),
  setReportTemplate: (reportTemplate) => set({ reportTemplate }),

  toggleDimension: (dim) => {
    const { selectedDimensions } = get();
    set({
      selectedDimensions: selectedDimensions.includes(dim)
        ? selectedDimensions.filter((d) => d !== dim)
        : [...selectedDimensions, dim],
    });
  },

  setAuthor: (author) => set({ author }),
  setReportDate: (reportDate) => set({ reportDate }),
  setReportData: (reportData) => set({ reportData }),
  setReportLoading: (reportLoading) => set({ reportLoading }),

  reset: () => set({ ...initialState, selectedYears: [String(new Date().getFullYear())] }),
}));
