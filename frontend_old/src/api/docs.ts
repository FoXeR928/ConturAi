import {
  API_BASE,
  ApiError,
  getToken,
  redirectToLogin,
  request,
} from './http';

// ==============================================================================
// БЛОК 1: БАЗОВЫЕ ОПЕРАЦИИ С ДОКУМЕНТАМИ (CRUD)
// ==============================================================================

export const docsApi = {
  /** Получить список всех загруженных документов (доступно админу) */
  listDocs: () => request('/ai/docs/list'),

  /** 
   * Загрузить файл на сервер для парсинга (извлечения текста). 
   * Использует FormData, так как передается бинарный файл.
   */
  readDoc: async (file: File) => {
    const fd = new FormData();
    fd.append('doc', file);
    return request('/ai/docs/read', { method: 'POST', body: fd });
  },

  /** 
   * Добавить документ в RAG (векторную базу). 
   * Можно передать готовый текст или указать upload_id (если текст уже извлечен из файла).
   */
  addDoc: (name: string, text: string, uploadId?: string, tags: string[] = []) =>
    request('/ai/docs/create', {
      method: 'POST',
      body: JSON.stringify({ name, text, upload_id: uploadId, tags }),
    }),

  /** Удалить документ (и его чанки из RAG) по его ID */
  deleteDoc: (uploadId: string) =>
    request(`/ai/docs/${uploadId}`, { method: 'DELETE' }),


// ==============================================================================
// БЛОК 2: СКАЧИВАНИЕ ОРИГИНАЛЬНОГО ФАЙЛА (DOWNLOAD)
// ==============================================================================

  /**
   * Скачивание файла (PDF, DOCX и т.д.).
   * 
   * Почему не используется стандартный `request()`?
   * Потому что нам нужен доступ к "сырому" ответу (Blob) и заголовкам (Content-Disposition),
   * а `request()` сразу парсит ответ как JSON.
   */
  downloadDoc: async (uploadId: string, fallbackName: string) => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/ai/docs/${uploadId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    // --- ШАГ 1: ОБРАБОТКА ОШИБОК АВТОРИЗАЦИИ ---
    // Если токен истек (401), разлогиниваем и отправляем на страницу входа.
    if (res.status === 401) {
      redirectToLogin();
      return;
    }

    // --- ШАГ 2: ОБРАБОТКА БИЗНЕС-ОШИБОК (403, 404, 500) ---
    // Если сервер вернул ошибку, пытаемся прочитать её из JSON и показать пользователю.
    if (!res.ok) {
      let message = `Не удалось скачать файл (HTTP ${res.status})`;
      try {
        const data = await res.json();
        if (data?.message) message = data.message;
      } catch {
        /* не JSON — оставляем дефолтное сообщение */
      }
      throw new ApiError(message, res.status);
    }

    // --- ШАГ 3: ЗАЩИТА ОТ "JSON ВМЕСТО ФАЙЛА" ---
    // Бывает, что сервер отвечает 200 OK, но внутри возвращает JSON с ошибкой.
    // Если мы этого не проверим, пользователь скачает файл с текстом ошибки.
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

    // --- ШАГ 4: ИЗВЛЕЧЕНИЕ ИМЕНИ ФАЙЛА (CONTENT-DISPOSITION) ---
    // Бэкенд может прислать имя в двух форматах:
    // 1. filename*=UTF-8''... (RFC 5987, правильная поддержка кириллицы)
    // 2. filename="..." (обычный ASCII, может сломаться на кириллице)
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

    // --- ШАГ 5: СОЗДАНИЕ ФАЙЛА И СКАЧИВАНИЕ ---
    const blob = await res.blob();
    
    // Защита: если файл на диске весит 0 байт
    if (blob.size === 0) {
      throw new ApiError(
        'Файл пустой (0 байт) — возможно, он удалён с диска',
        res.status
      );
    }

    // Создаем временную ссылку в памяти браузера на этот файл
    const url = URL.createObjectURL(blob);
    
    // Создаем невидимую ссылку <a> и программно кликаем по ней
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadName;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();

    // --- ШАГ 6: ОЧИСТКА ПАМЯТИ ---
    // ВАЖНО: Нельзя удалять ObjectURL сразу. 
    // Браузеру нужно время, чтобы начать загрузку файла в фоне.
    // Поэтому ставим задержку в 1 секунду.
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1000);
  },
};