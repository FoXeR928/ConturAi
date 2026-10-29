import { describe, it, expect, beforeEach, vi } from 'vitest';
import { docsApi } from '../src/api/docs';
import { ApiError } from '../src/api/http';

describe('docsApi.downloadDoc', () => {
  let anchor: HTMLAnchorElement | null = null;

  beforeEach(() => {
    anchor = null;
    // Blob URL API в jsdom отсутствует
    (URL as any).createObjectURL = vi.fn(() => 'blob:mock');
    (URL as any).revokeObjectURL = vi.fn();

    const realCreate = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      const el = realCreate(tag) as HTMLElement;
      if (tag === 'a') {
        (el as HTMLAnchorElement).click = vi.fn();
        anchor = el as HTMLAnchorElement;
      }
      return el;
    });
  });

  it('успешно скачивает и берёт имя из filename*= (UTF-8)', async () => {
    localStorage.setItem('token', 'tok');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('PDF-CONTENT', {
        status: 200,
        headers: {
          'Content-Type': 'application/pdf',
          'Content-Disposition': "attachment; filename*=UTF-8''%D0%B4%D0%BE%D0%BA.pdf",
        },
      })
    ));

    await docsApi.downloadDoc('id1', 'fallback.pdf');

    expect(anchor).not.toBeNull();
    expect(anchor!.download).toBe('док.pdf');
    expect(anchor!.click).toHaveBeenCalledTimes(1);
  });

  it('использует filename из Content-Disposition (plain)', async () => {
    localStorage.setItem('token', 'tok');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('x', {
        status: 200,
        headers: {
          'Content-Type': 'text/plain',
          'Content-Disposition': 'attachment; filename="doc.txt"',
        },
      })
    ));

    await docsApi.downloadDoc('id1', 'fallback.txt');
    expect(anchor!.download).toBe('doc.txt');
  });

  it('кидает ApiError с message из JSON при 404', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'У этого документа нет оригинала' }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      })
    ));

    await expect(docsApi.downloadDoc('id1', 'x.pdf'))
      .rejects.toMatchObject({ message: 'У этого документа нет оригинала', status: 404 });
  });

  it('кидает ApiError, если 200, но пришёл JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'Странный ответ' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    ));

    await expect(docsApi.downloadDoc('id1', 'x.pdf')).rejects.toThrow('Странный ответ');
  });

  it('кидает ApiError на пустой файл (0 байт)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response('', {
        status: 200,
        headers: { 'Content-Type': 'application/pdf' },
      })
    ));

    await expect(docsApi.downloadDoc('id1', 'x.pdf')).rejects.toThrow(/пустой/);
  });

  it('при 401 чистит auth и не открывает диалог скачивания', async () => {
    localStorage.setItem('token', 'tok');
    localStorage.setItem('me', '{}');

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'expired' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      })
    ));

    await docsApi.downloadDoc('id1', 'x.pdf');

    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('me')).toBeNull();
    expect(anchor).toBeNull();
  });
});