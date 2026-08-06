import apiClient from './client';

export interface RecommendationListItem {
  recommendation_id: string;
  recommendation_type: string;
  sku_id: string;
  sku_name: string;
  lot_id?: string | null;
  source_location_id?: string | null;
  source_location_name?: string | null;
  target_location_id?: string | null;
  target_location_name?: string | null;
  proposed_qty: number;
  adjusted_qty?: number | null;
  effective_qty: number;
  reason: string;
  status: string;
  created_at: string;
  data_status: string;
}

export interface RecommendationSummaryCounts {
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  total_count: number;
}

export interface RecommendationListResponse {
  items: RecommendationListItem[];
  total: number;
  summary: RecommendationSummaryCounts;
}

export interface RecommendationAuditItem {
  audit_id: string;
  recommendation_id: string;
  actor_username: string;
  action: string;
  before_status: string;
  after_status: string;
  comment?: string | null;
  action_timestamp: string;
  data_status: string;
}

export interface RecommendationDetailResponse {
  recommendation_id: string;
  recommendation_type: string;
  sku_id: string;
  sku_name: string;
  category: string;
  pack_size?: string | null;
  lot_id?: string | null;
  expiry_date?: string | null;
  days_to_expiry?: number | null;
  source_location_id?: string | null;
  source_location_name?: string | null;
  target_location_id?: string | null;
  target_location_name?: string | null;
  proposed_qty: number;
  adjusted_qty?: number | null;
  effective_qty: number;
  reason: string;
  status: string;
  created_at: string;
  data_status: string;
  audit_history: RecommendationAuditItem[];
}

export interface RecommendationFilterParams {
  status?: string;
  recommendation_type?: string;
  sku_id?: string;
  lot_id?: string;
  search?: string;
}

export async function getRecommendations(params?: RecommendationFilterParams): Promise<RecommendationListResponse> {
  const res = await apiClient.get<RecommendationListResponse>('/api/recommendations', { params });
  return res.data;
}

export async function getRecommendationDetail(id: string): Promise<RecommendationDetailResponse> {
  const res = await apiClient.get<RecommendationDetailResponse>(`/api/recommendations/${id}`);
  return res.data;
}

export async function modifyRecommendationQuantity(
  id: string,
  adjusted_qty: number,
  comment: string
): Promise<RecommendationDetailResponse> {
  const res = await apiClient.patch<RecommendationDetailResponse>(`/api/recommendations/${id}/quantity`, {
    adjusted_qty,
    comment,
  });
  return res.data;
}

export async function approveRecommendation(
  id: string,
  comment: string
): Promise<RecommendationDetailResponse> {
  const res = await apiClient.post<RecommendationDetailResponse>(`/api/recommendations/${id}/approve`, {
    comment,
  });
  return res.data;
}

export async function rejectRecommendation(
  id: string,
  comment: string
): Promise<RecommendationDetailResponse> {
  const res = await apiClient.post<RecommendationDetailResponse>(`/api/recommendations/${id}/reject`, {
    comment,
  });
  return res.data;
}
