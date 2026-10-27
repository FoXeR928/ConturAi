import { request } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ (TYPESCRIPT INTERFACES)
// ==============================================================================

export interface DownloadRequestItem {
  id: string;
  user_login: string;
  original_name: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  expires_at?: string | null;
}

export interface RequestsResponse {
  result: boolean;
  requests: DownloadRequestItem[];
}

// ==============================================================================
// БЛОК 2: ЗАПРОСЫ СО СТОРОНЫ ПОЛЬЗОВАТЕЛЯ
// ==============================================================================

export const downloadsApi = {
  /**
   * Отправляет заявку администратору на получение доступа к скачиванию файла.
   * 
   * @param uploadId - UUID документа, который пользователь хочет скачать.
   * 
   * На бэкенде создается запись в таблице `download_requests` со статусом 'pending' (в ожидании).
   * Если пользователь повторно нажмет на кнопку, бэкенд вернет ошибку 400 (заявка уже существует).
   */
  requestAccess: (uploadId: string) => request('/downloads/request', {
    method: 'POST',
    body: JSON.stringify({ upload_id: uploadId }),
  }),


// ==============================================================================
// БЛОК 3: УПРАВЛЕНИЕ ЗАЯВКАМИ СО СТОРОНЫ АДМИНИСТРАТОРА
// ==============================================================================

  /**
   * Получает список всех заявок на скачивание (доступно только админам).
   * 
   * Используется в админ-панели для отрисовки таблицы: 
   * кто запросил (user_login), какой файл (original_name) и когда (created_at).
   * Возвращает типизированный ответ `RequestsResponse`.
   */
  listRequests: () => request<RequestsResponse>('/downloads/list'),
  
  /**
   * Обрабатывает заявку (одобряет или отклоняет).
   * 
   * @param requestId - UUID самой заявки (не файла!).
   * @param action - 'approve' (одобрить) или 'reject' (отклонить).
   * 
   * Если выбрано 'approve', бэкенд установит статус 'approved' и 
   * выдаст доступ на 24 часа (поле expires_at).
   * Если 'reject', пользователь больше не сможет скачать файл (до новой заявки).
   */
  processRequest: (requestId: string, action: 'approve' | 'reject') => request('/downloads/action', {
    method: 'POST',
    body: JSON.stringify({ request_id: requestId, action }),
  }),
};