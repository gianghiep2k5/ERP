import apiClient from './client';

export interface AuditListItem {
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

export interface AuditListResponse {
  items: AuditListItem[];
  total: number;
}

export interface AuditFilterParams {
  recommendation_id?: string;
  actor_username?: string;
  action?: string;
  start_date?: string;
  end_date?: string;
}

export async function getAuditLogs(params?: AuditFilterParams): Promise<AuditListResponse> {
  const res = await apiClient.get<AuditListResponse>('/api/audit', { params });
  return res.data;
}

export async function getAuditLogDetail(auditId: string): Promise<AuditListItem> {
  const res = await apiClient.get<AuditListItem>(`/api/audit/${auditId}`);
  return res.data;
}
