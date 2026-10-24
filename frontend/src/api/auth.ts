import { API_BASE, ApiError, clearAuth, parseErrorResponse } from './http';

export async function login(username: string, password: string) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });

  const data = await parseErrorResponse(res);

  if (!res.ok) {
    throw new ApiError(
      data.message || `Ошибка входа: HTTP ${res.status}`,
      res.status,
      data.category
    );
  }

  if (!data.access_token) {
    throw new ApiError('Сервер не вернул токен авторизации', res.status);
  }

  localStorage.setItem('token', data.access_token);
  return data as {
    access_token: string;
    token_type: string;
    message?: string;
    category?: string;
  };
}

export function logout(): void {
  clearAuth();
}