import apiClient from './client';

export interface ForecastSKUListItem {
  sku_id: string;
  sku_name: string;
  category: string;
  forecast_run_id: string;
  wape: number;
  bias: number;
  model_name: string;
  review_status?: string | null;
}

export interface SalesObservation {
  sales_date: string;
  quantity_sold: number;
}

export interface ForecastObservation {
  forecast_date: string;
  forecast_qty: number;
}

export interface ReviewItem {
  review_id: string;
  forecast_run_id: string;
  reviewer_username: string;
  review_status: string;
  planner_comment: string;
  reviewed_at: string;
}

export interface ForecastSKUDetailResponse {
  sku_id: string;
  sku_name: string;
  category: string;
  analysis_date: string;
  actual_start_date: string;
  actual_end_date: string;
  actual_sales: SalesObservation[];
  forecast_start_date: string;
  forecast_end_date: string;
  forecast_results: ForecastObservation[];
  forecast_run_id: string;
  model_name: string;
  wape: number;
  bias: number;
  evaluation_window_days: number;
  latest_review?: ReviewItem | null;
  review_history: ReviewItem[];
}

export interface CreateReviewPayload {
  review_status: string;
  planner_comment: string;
}

export async function getForecastSKUs(): Promise<ForecastSKUListItem[]> {
  const res = await apiClient.get<ForecastSKUListItem[]>('/api/forecast/skus');
  return res.data;
}

export async function getForecastSKUDetail(skuId: string): Promise<ForecastSKUDetailResponse> {
  const res = await apiClient.get<ForecastSKUDetailResponse>(`/api/forecast/${skuId}`);
  return res.data;
}

export async function submitPlannerReview(skuId: string, payload: CreateReviewPayload): Promise<ReviewItem> {
  const res = await apiClient.post<ReviewItem>(`/api/forecast/${skuId}/review`, payload);
  return res.data;
}
