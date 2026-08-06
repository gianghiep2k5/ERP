import apiClient from './client';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
}

export interface MeResponse {
  user_id: string;
  username: string;
  role: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await apiClient.post<LoginResponse>('/api/auth/login', { username, password });
  return res.data;
}

export async function getMe(token?: string): Promise<MeResponse> {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const res = await apiClient.get<MeResponse>('/api/auth/me', { headers });
  return res.data;
}
