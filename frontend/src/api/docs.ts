import {
  API_BASE,
  ApiError,
  getToken,
  redirectToLogin,
  request,
} from './http';

export const docsApi = {
  listDocs: () => request('/ai/docs/list'),

  readDoc: async (file: File) => {
    const fd = new FormData();
    fd.append('doc', file);
    return request('/ai/docs/read', { method: 'POST', body: fd });
  },

  addDoc: (name: string, text: string, uploadId?: string) =>
    request('/ai/docs/create', {
      method: 'POST',
      body: JSON.stringify({ name, text, upload_id: uploadId }),
    }),

  deleteDoc: (uploadId: string) =>
    request(`/ai/docs/${uploadId}`, { method: 'DELETE' }),

  downloadDoc: async (uploadId: string, fallbackName: string) => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/ai/docs/${uploadId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    // 401 — разлогиниваем и на главную
    if (res.status === 401) {
      redirectToLogin();
      return;
    }

    // Ошибка — вытаскиваем message из JSON-ответа бэка
    if (!res.ok) {
      let message = `Не удалось скачать файл (HTTP ${res.status})`;
      try {
        const data = await res.json();
        if (data?.message) message = data.message;
      } catch {
        /* не JSON — оставляем дефолт */
      }
      throw new ApiError(message, res.status);
    }

    // Защита: сервер вернул JSON вместо файла
    const contentType = res.headers.get('Content-Type') || '';
    if (contentType.includes('application/json')) {
      let message = 'Сервер вернул JSON вместо файла';
      try {
        const data = await res.json();
        if (data?.message) message = data.message;
      } catch {
        /* ignore */
      }
      throw new ApiError(message, res.status);
    }

    // Имя: UTF-8 (RFC 5987) → обычный filename → fallback
    const cd = res.headers.get('Content-Disposition') || '';
    let downloadName = fallbackName || 'download';

    const utf8Match = /filename\*=(?:UTF-8|utf-8)''([^;]+)/.exec(cd);
    const plainMatch = /filename="?([^";]+)"?/i.exec(cd);

    if (utf8Match) {
      try {
        downloadName = decodeURIComponent(utf8Match[1].trim());
      } catch {
        /* ignore */
      }
    } else if (plainMatch) {
      downloadName = plainMatch[1].trim();
    }

    const blob = await res.blob();
    if (blob.size === 0) {
      throw new ApiError(
        'Файл пустой (0 байт) — возможно, он удалён с диска',
        res.status
      );
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadName;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();

    // Отложенная очистка — браузеру нужно время начать загрузку
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1000);
  },
};