import { create } from 'zustand';

interface ComparisonBasket {
  indicatorIds: string[];
  companyNames: string[];
  addIndicator: (id: string) => void;
  removeIndicator: (id: string) => void;
  addCompany: (name: string) => void;
  removeCompany: (name: string) => void;
  clearAll: () => void;
}

export const useComparisonBasket = create<ComparisonBasket>((set) => ({
  indicatorIds: [],
  companyNames: [],
  addIndicator: (id) =>
    set((s) => ({
      indicatorIds: s.indicatorIds.includes(id) ? s.indicatorIds : [...s.indicatorIds, id],
    })),
  removeIndicator: (id) =>
    set((s) => ({ indicatorIds: s.indicatorIds.filter((i) => i !== id) })),
  addCompany: (name) =>
    set((s) => ({
      companyNames: s.companyNames.includes(name) ? s.companyNames : [...s.companyNames, name],
    })),
  removeCompany: (name) =>
    set((s) => ({ companyNames: s.companyNames.filter((c) => c !== name) })),
  clearAll: () => set({ indicatorIds: [], companyNames: [] }),
}));
