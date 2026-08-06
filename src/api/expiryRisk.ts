import apiClient from './client';

export interface ExpiryRiskItem {
  inventory_id: string;
  lot_id: string;
  sku_id: string;
  sku_name: string;
  category: string;
  location_id: string;
  location_name: string;
  available_qty: number;
  on_hand_qty: number;
  manufacturing_date: string;
  expiry_date: string;
  analysis_date: string;
  days_to_expiry: number;
  recent_30d_sales_qty: number;
  recent_average_daily_demand: number;
  forecast_consumption_before_expiry: number;
  forecast_method: string;
  projected_surplus: number;
  projected_shortage: number;
  surplus_ratio: number;
  urgency_factor: number;
  risk_score: number;
  risk_band: 'Expired' | 'Critical' | 'High' | 'Medium' | 'Low';
  explanation: string;
  proposed_actions: string[];
  fefo_position: number;
  related_recommendation_ids: string[];
  pack_size?: string | null;
  public_product_id?: string | null;
  product_name?: string | null;
  source_url?: string | null;
}

export interface ExpiryRiskSummaryCounts {
  expired_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_projected_surplus: number;
}

export interface ExpiryRiskListResponse {
  items: ExpiryRiskItem[];
  total: number;
  summary: ExpiryRiskSummaryCounts;
}

export interface ExpiryRiskFilterParams {
  risk_band?: string;
  sku_id?: string;
  category?: string;
  location_id?: string;
  expiry_bucket?: string;
  search?: string;
}

export async function getExpiryRiskList(params?: ExpiryRiskFilterParams): Promise<ExpiryRiskListResponse> {
  const res = await apiClient.get<ExpiryRiskListResponse>('/api/expiry-risk', { params });
  return res.data;
}

export async function getExpiryRiskDetail(lotId: string): Promise<ExpiryRiskItem> {
  const res = await apiClient.get<ExpiryRiskItem>(`/api/expiry-risk/${lotId}`);
  return res.data;
}
