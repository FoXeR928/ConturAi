const TOKEN_KEY = 'conturai_token';
const API_BASE = '/api/v1';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

interface ApiErrorBody {
  error?: { code?: string; message?: string };
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  const token = getToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 401) {
    clearToken();
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new ApiError('UNAUTHORIZED', 'Требуется авторизация', 401);
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorBody;
    const code = body.error?.code ?? 'HTTP_ERROR';
    const message = body.error?.message ?? `HTTP ${response.status}`;
    throw new ApiError(code, message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}