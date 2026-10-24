export const API_BASE = '/api';

export interface ApiErrorPayload {
  result?: boolean;
  message?: string;
  category?: string;
}

export class ApiError extends Error {
  status: number;
  category?: string;

  constructor(message: string, status: number, category?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.category = category;
  }
}

export function getToken(): string | null {
  return localStorage.getItem('token');
}

export function clearAuth(): void {
  localStorage.removeItem('token');
  localStorage.removeItem('me');
}

export function redirectToLogin(): void {
  clearAuth();
  if (window.location.pathname !== '/') {
    window.location.href = '/';
  }
}

/** Разбирает тело ответа как JSON. Если не JSON — возвращает объект с сообщением. */
export async function parseErrorResponse(res: Response): Promise<Record<string, any>> {
  const text = await res.text();
  if (!text) {
    return { message: `HTTP ${res.status} ${res.statusText}`.trim() };
  }
  try {
    return JSON.parse(text);
  } catch {
    return {
      message: `Ошибка сервера: HTTP ${res.status} ${res.statusText}`.trim(),
      category: 'error',
    };
  }
}

export interface RequestOptions extends RequestInit {
  /** Не редиректить на логин при 401 (используется в login-запросе). */
  skipAuthRedirect?: boolean;
}

export async function request<T = any>(
  path: string,
  opts: RequestOptions = {}
): Promise<T> {
  const { skipAuthRedirect, ...init } = opts;

  const headers: Record<string, string> = {
    ...((init.headers as Record<string, string>) || {}),
  };

  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const isFormData = init.body instanceof FormData;
  if (!isFormData && init.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const text = await res.text();

  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = {
        result: false,
        message: `Ошибка сервера: HTTP ${res.status} ${res.statusText}`.trim(),
        category: 'error',
      };
    }
  }

  if (!res.ok) {
    if (res.status === 401 && !skipAuthRedirect) {
      redirectToLogin();
    }
    throw new ApiError(
      data.message || `HTTP ${res.status}`,
      res.status,
      data.category
    );
  }

  return data as T;
}