import { API_BASE, ApiError, clearAuth, parseErrorResponse } from './http';

// ==============================================================================
// БЛОК 1: АВТОРИЗАЦИЯ (ВХОД В СИСТЕМУ)
// ==============================================================================

export async function login(username: string, password: string, rememberMe: boolean = false) {
  // 1. Подготовка данных для отправки.
  // ВАЖНО: Бэкенд использует OAuth2PasswordRequestForm (стандарт FastAPI), 
  // поэтому данные должны передаваться не в JSON, а как application/x-www-form-urlencoded.
  // Для этого используем встроенный класс URLSearchParams.
  const form = new URLSearchParams();
  form.append('username', username);
  form.append('password', password);

  // Передаем флаг как form-data, так как эндпоинт ожидает OAuth2PasswordRequestForm
  form.append('expires_use', rememberMe ? 'true' : 'false');

  // 2. Отправка запроса на сервер.
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });

  // 3. Безопасный парсинг ответа.
  // Мы не используем res.json() напрямую, так как если сервер упадет (500 ошибка),
  // он может вернуть HTML-страницу, и res.json() выбросит исключение SyntaxError.
  // parseErrorResponse гарантирует, что мы получим объект в любом случае.
  const data = await parseErrorResponse(res);

  // 4. Обработка ошибок HTTP (401, 422, 500).
  if (!res.ok) {
    throw new ApiError(
      data.message || `Ошибка входа: HTTP ${res.status}`,
      res.status,
      data.category
    );
  }

  // 5. Проверка, что сервер действительно вернул токен.
  if (!data.access_token) {
    throw new ApiError('Сервер не вернул токен авторизации', res.status);
  }

  // 6. Сохранение токена.
  // Используем localStorage, чтобы пользователь оставался в системе 
  // после перезагрузки страницы или закрытия вкладки.
  localStorage.setItem('token', data.access_token);

  // 7. Возврат типизированных данных.
  // TypeScript будет знать, что отсюда возвращается access_token и token_type.
  return data as {
    access_token: string;
    token_type: string;
    message?: string;
    category?: string;
  };
}


// ==============================================================================
// БЛОК 2: ДЕАВТОРИЗАЦИЯ (ВЫХОД ИЗ СИСТЕМЫ)
// ==============================================================================

export function logout(): void {
  // JWT-токены являются stateless (сервер их не запоминает).
  // Поэтому для выхода достаточно просто удалить токен и данные пользователя 
  // из браузера. Функция clearAuth() (из http.ts) делает именно это.
  clearAuth();
}