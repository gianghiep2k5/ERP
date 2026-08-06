import apiClient from './client';

export interface LinkedRecommendation {
  recommendation_id: string;
  recommendation_type: string;
  proposed_qty: number;
  adjusted_qty: number | null;
  effective_qty: number;
  status: string;
  reason: string;
  created_at: string;
}

export interface LotDetail {
  lot_id: string;
  manufacturing_date: string;
  expiry_date: string;
  days_to_expiry: number;
  fefo_position: number;
  fefo_total: number;
  lot_data_status: string;
  sku_id: string;
  sku_name: string;
  category: string;
  pack_size: string | null;
  default_shelf_life_days: number;
  unit_cost_vnd: number;
  variant_status: string;
  source_status: string;
  public_product_id: string;
  product_name: string;
  public_pack_size: string | null;
  source_url: string;
  inventory_id: string;
  location_id: string;
  location_name: string;
  location_type: string;
  on_hand_qty: number;
  available_qty: number;
  reserved_qty: number;
  quarantine_qty: number;
  last_updated: string;
  scenario: string;
  recommendations: LinkedRecommendation[];
  analysis_date: string;
}

export async function getLotDetail(lotId: string): Promise<LotDetail> {
  const res = await apiClient.get<LotDetail>(`/api/lots/${lotId}`);
  return res.data;
}
