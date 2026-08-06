import apiClient from './client';

export interface DashboardSummary {
  total_skus: number;
  total_lots: number;
  total_on_hand_qty: number;
  pending_recommendations: number;
  stockout_count: number;
  expiry_count: number;
  transfer_count: number;
  normal_count: number;
  latest_update: string | null;
  analysis_date: string;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const res = await apiClient.get<DashboardSummary>('/api/dashboard/summary');
  return res.data;
}
