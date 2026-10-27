import { request } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

export interface DownloadRequestItem {
  id: string;
  user_login: string;
  status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  expires_at?: string | null;
  file_name?: string | null; // для документов
  chat_name?: string | null; // для чатов
}

export interface RequestsResponse {
  result: boolean;
  requests: DownloadRequestItem[];
}

// ==============================================================================
// БЛОК 2: API ДЛЯ СКАЧИВАНИЯ
// ==============================================================================

export const downloadsApi = {
  /**
   * Отправляет заявку на скачивание (файла или чата).
   */
  requestAccess: (params: { uploadId?: string; chatId?: string }) => 
    request('/downloads/request', {
      method: 'POST',
      body: JSON.stringify({ 
        upload_id: params.uploadId, 
        chat_id: params.chatId 
      }),
    }),

  /**
   * Получает список всех заявок (для админа).
   */
  listRequests: () => request<RequestsResponse>('/downloads/list'),
  
  /**
   * Обрабатывает заявку ('approve' | 'reject').
   */
  processRequest: (requestId: string, action: 'approve' | 'reject') => 
    request('/downloads/action', {
      method: 'POST',
      body: JSON.stringify({ request_id: requestId, action }),
    }),
};