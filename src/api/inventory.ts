import apiClient from './client';

export interface InventoryItem {
  inventory_id: string;
  lot_id: string;
  sku_id: string;
  sku_name: string;
  category: string;
  pack_size: string | null;
  location_id: string;
  location_name: string;
  on_hand_qty: number;
  available_qty: number;
  reserved_qty: number;
  quarantine_qty: number;
  manufacturing_date: string;
  expiry_date: string;
  days_to_expiry: number;
  fefo_priority: number;
  scenario: string;
  data_status: string;
}

export interface InventoryListResponse {
  items: InventoryItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface InventoryFilterParams {
  sku_id?: string;
  category?: string;
  scenario?: string;
  location_id?: string;
  expiry_bucket?: string;
  skip?: number;
  limit?: number;
}

export async function getInventoryList(params?: InventoryFilterParams): Promise<InventoryListResponse> {
  const res = await apiClient.get<InventoryListResponse>('/api/inventory', { params });
  return res.data;
}

export async function getInventoryDetail(id: string): Promise<InventoryItem> {
  const res = await apiClient.get<InventoryItem>(`/api/inventory/${id}`);
  return res.data;
}
