import { describe, it, expect, beforeEach, vi } from 'vitest';
import { request, ApiError } from '../src/api/http';

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

describe('http.request', () => {
  it('возвращает JSON при 200', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ result: true, data: 'ok' })));

    const data = await request<{ result: boolean; data: string }>('/test');
    expect(data.result).toBe(true);
    expect(data.data).toBe('ok');
  });

  it('возвращает {} при пустом body', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 200 })));
    const data = await request('/test');
    expect(data).toEqual({});
  });

  it('кидает ApiError с message от сервера при 4xx', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      jsonResponse({ result: false, message: 'Неверный логин', category: 'warning' }, 401)
    ));

    await expect(request('/test', { skipAuthRedirect: true })).rejects.toMatchObject({
      name: 'ApiError',
      message: 'Неверный логин',
      status: 401,
      category: 'warning',
    });
  });

  it('кидает ApiError с fallback-сообщением при HTML-ответе 500', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('<html>500</html>', {
        status: 500,
        statusText: 'Internal Server Error',
        headers: { 'Content-Type': 'text/html' },
      })
    ));

    await expect(request('/test')).rejects.toThrow(/Ошибка сервера.*500/);
  });

  it('при 401 чистит localStorage и кидает ApiError', async () => {
    localStorage.setItem('token', 'abc');
    localStorage.setItem('me', '{}');

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      jsonResponse({ message: 'expired' }, 401)
    ));

    await expect(request('/test')).rejects.toBeInstanceOf(ApiError);
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('me')).toBeNull();
  });

  it('при 401 с skipAuthRedirect не чистит токен', async () => {
    localStorage.setItem('token', 'abc');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      jsonResponse({ message: 'bad creds' }, 401)
    ));

    await expect(request('/test', { skipAuthRedirect: true })).rejects.toBeInstanceOf(ApiError);
    expect(localStorage.getItem('token')).toBe('abc');
  });

  it('передаёт Authorization, если есть токен', async () => {
    localStorage.setItem('token', 'my-token');
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal('fetch', fetchMock);

    await request('/test');

    const [, init] = fetchMock.mock.calls[0];
    expect((init.headers as Record<string, string>)['Authorization']).toBe('Bearer my-token');
  });

  it('не ставит Content-Type для FormData', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal('fetch', fetchMock);

    const fd = new FormData();
    fd.append('x', 'y');
    await request('/test', { method: 'POST', body: fd });

    const [, init] = fetchMock.mock.calls[0];
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined();
  });

  it('ставит Content-Type application/json для строкового body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal('fetch', fetchMock);

    await request('/test', { method: 'POST', body: JSON.stringify({ a: 1 }) });

    const [, init] = fetchMock.mock.calls[0];
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
  });
});