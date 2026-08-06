import axios from 'axios';

export const TOKEN_KEY = 'vims_token';

/**
 * Central authenticated Axios client for all V-IMS AI API calls.
 * Automatically attaches `Authorization: Bearer <token>` to requests
 * when a token exists in localStorage under `vims_token`.
 * Intercepts 401 response errors to clear stale tokens and trigger re-auth.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10_000,
});

// Request interceptor: attach bearer token automatically if present
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 Unauthorized globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    return Promise.reject(error);
  }
);

export default apiClient;
