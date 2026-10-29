const API_BASE = '/api';

export const getToken = () => localStorage.getItem('token');
export const clearAuth = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('me');
};

export async function request<T = any>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { ...(options.headers as any) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && options.body) headers['Content-Type'] = 'application/json';

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const text = await res.text();
  
  let data: any = {};
  if (text) {
    try { data = JSON.parse(text); } catch { throw new Error(`Ошибка сервера: HTTP ${res.status}`); }
  }

  if (!res.ok) {
    if (res.status === 401) { clearAuth(); window.location.href = '/'; }
    throw new Error(data.message || `HTTP ${res.status}`);
  }
  return data as T;
}