import { create } from 'zustand';
import type { OverviewData, DataStats } from '../types';

interface AppState {
  overview: OverviewData | null;
  stats: DataStats | null;
  loading: boolean;
  setOverview: (data: OverviewData) => void;
  setStats: (data: DataStats) => void;
  setLoading: (loading: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  overview: null,
  stats: null,
  loading: false,
  setOverview: (overview) => set({ overview }),
  setStats: (stats) => set({ stats }),
  setLoading: (loading) => set({ loading }),
}));
