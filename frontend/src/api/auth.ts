import { request, clearAuth } from './http';

export async function login(username: string, password: string, rememberMe: boolean) {
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);
  form.append('expires_use', rememberMe ? 'true' : 'false');

  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Ошибка входа');
  
  localStorage.setItem('token', data.access_token);
  return data;
}

export function logout() { clearAuth(); }