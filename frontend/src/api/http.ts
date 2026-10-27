// ==============================================================================
// БЛОК 1: КОНСТАНТЫ И КЛАССЫ ОШИБОК
// ==============================================================================

export const API_BASE = '/api';

export interface ApiErrorPayload {
  result?: boolean;
  message?: string;
  category?: string;
}

/**
 * Кастомный класс ошибки для всего приложения.
 * Позволяет отличать сетевые ошибки от логических.
 * Содержит HTTP-статус и категорию ('error' или 'warning' для UI).
 */
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


// ==============================================================================
// БЛОК 2: УТИЛИТЫ АВТОРИЗАЦИИ И БЕЗОПАСНОСТИ
// ==============================================================================

/** Получает JWT-токен из локального хранилища браузера. */
export function getToken(): string | null {
  return localStorage.getItem('token');
}

/** Полностью очищает данные авторизации (токен и профиль пользователя). */
export function clearAuth(): void {
  localStorage.removeItem('token');
  localStorage.removeItem('me');
}

/** 
 * Принудительный разлогин.
 * Очищает данные и перенаправляет на страницу входа.
 * Используется при истечении токена (401).
 */
export function redirectToLogin(): void {
  clearAuth();
  // Проверяем, чтобы не было бесконечного цикла, если мы уже на странице логина
  if (window.location.pathname !== '/') {
    window.location.href = '/';
  }
}


// ==============================================================================
// БЛОК 3: БЕЗОПАСНЫЙ ПАРСИНГ ОШИБОК
// ==============================================================================

/** 
 * Разбирает тело ответа как JSON. Если пришел HTML (например, 502 от Nginx) 
 * или пустая строка — возвращает объект с понятным сообщением.
 */
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


// ==============================================================================
// БЛОК 4: ГЛАВНЫЙ HTTP-КЛИЕНТ (WRAPPER)
// ==============================================================================

export interface RequestOptions extends RequestInit {
  /** Не редиректить на логин при 401 (используется в login-запросе). */
  skipAuthRedirect?: boolean;
}

/**
 * Универсальная функция для всех API-запросов.
 * Автоматически:
 * 1. Добавляет JWT-токен.
 * 2. Ставит правильный Content-Type (JSON или multipart/form-data).
 * 3. Перехватывает 401 (разлогинивает).
 * 4. Превращает ошибки сервера в объекты ApiError.
 * 
 * @param path - Путь к эндпоинту (например, '/users/get').
 * @param opts - Опции fetch (метод, body, headers и т.д.).
 * @param opts.skipAuthRedirect - Если true, не будет редиректа при 401 (нужно для самой формы логина).
 */
export async function request<T = any>(
  path: string,
  opts: RequestOptions = {}
): Promise<T> {
  // Отделяем кастомный флаг от стандартных опций fetch
  const { skipAuthRedirect, ...init } = opts;

  // 1. Подготовка заголовков
  const headers: Record<string, string> = {
    ...((init.headers as Record<string, string>) || {}),
  };

  // Добавляем токен, если он есть
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  // 2. Умная установка Content-Type
  // Если отправляем файл (FormData), браузер сам установит заголовок с boundary.
  // Если ставим его вручную — загрузка файла сломается.
  // Если отправляем обычный текст/объект — ставим application/json.
  const isFormData = init.body instanceof FormData;
  if (!isFormData && init.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // 3. Выполнение запроса
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  
  // Читаем ответ как текст, а не как JSON.
  // Это защищает от падения, если сервер вернет HTML (например, при ошибке 500).
  const text = await res.text();

  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      // Если пришел не JSON, формируем фейковый ответ с ошибкой
      data = {
        result: false,
        message: `Ошибка сервера: HTTP ${res.status} ${res.statusText}`.trim(),
        category: 'error',
      };
    }
  }

  // 4. Обработка ошибок HTTP
  if (!res.ok) {
    // Если сессия истекла (401) и это не запрос на логин — выкидываем на главную
    if (res.status === 401 && !skipAuthRedirect) {
      redirectToLogin();
    }
    
    // Выбрасываем ошибку наверх, чтобы компонент мог её поймать в try/catch
    throw new ApiError(
      data.message || `HTTP ${res.status}`,
      res.status,
      data.category
    );
  }

  // 5. Возврат успешного ответа
  return data as T;
}