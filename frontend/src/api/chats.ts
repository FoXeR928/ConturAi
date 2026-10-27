import { request, getToken, API_BASE } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ (TYPESCRIPT INTERFACES)
// ==============================================================================

export interface Chat {
  id: string;
  name: string;
  created_at?: string;
  user_login?: string;
}

export interface Message {
  id: string;
  chat_role: 'user' | 'assistant';
  text: string;
  created_at?: string;
}

// Типизация ответов от сервера
export interface ChatsResponse {
  result: boolean;
  chats: Chat[];
}

export interface MessagesResponse {
  result: boolean;
  chat_name: string;
  messages_history: Message[];
}

// ==============================================================================
// БЛОК 2: API ДЛЯ РАБОТЫ С ЧАТАМИ (CRUD)
// ==============================================================================

export const chatsApi = {
  /** Получить список всех активных чатов пользователя */
  getChats: () => request<ChatsResponse>('/chats/get'),

  /** Создать новый чат */
  createChat: (name: string) => 
    request<{ result: boolean; chat_id: string }>('/chats/create', { 
      method: 'POST', 
      body: JSON.stringify({ name }) 
    }),

  /** Переименовать чат */
  renameChat: (chatId: string, name: string) => 
    request(`/chats/rename?chat_id=${chatId}`, { 
      method: 'PATCH', 
      body: JSON.stringify({ name }) 
    }),

  /** Получить историю сообщений конкретного чата */
  getMessages: (chatId: string) => 
    request<MessagesResponse>(`/chats/messages/get?chat_id=${chatId}`),

  /** Удалить конкретное сообщение из чата */
  deleteMessage: (chatId: string, messageId: string) => 
    request(`/chats/messages/delete?chat_id=${chatId}&message_id=${messageId}`, { 
      method: 'DELETE' 
    }),

  // --- Корзина (Мягкое удаление и восстановление) ---
  
  /** Переместить чат в корзину (soft delete) */
  softDeleteChat: (chatId: string) => 
    request(`/chats/delete?chat_id=${chatId}`, { method: 'PATCH' }),
    
  /** Получить список чатов из корзины (только для админа) */
  getDeletedChats: () => 
    request<ChatsResponse>('/chats/delete/irrevocably/get'),

  // --- Безвозвратное удаление (только для админа) ---

  /** Удалить выбранные чаты из корзины навсегда */
  purgeDeletedChats: (chatIds: string[]) => 
    request('/chats/delete/irrevocably/list', { 
      method: 'DELETE', 
      body: JSON.stringify(chatIds) 
    }),
    
  /** Полностью очистить корзину */
  purgeAllDeletedChats: () => 
    request('/chats/delete/irrevocably/all', { method: 'DELETE' }),
    
  /** Восстановить чаты из корзины */
  recoverChats: (chatIds: string[]) => 
    request('/chats/recovery/list', { 
      method: 'PATCH', 
      body: JSON.stringify(chatIds) 
    }),

  // --- Экспорт (Скачивание файла) ---

  /** 
   * Скачать историю чата в формате Markdown.
   * Реализовано через fetch + Blob, так как это файл, а не JSON.
   */
  exportChat: async (chatId: string, fallbackName: string) => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/chats/export/${chatId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) {
      let errorMsg = 'Не удалось скачать чат';
      try {
        const data = await res.json();
        if (data.message) errorMsg = data.message;
      } catch (e) {}
      throw new Error(errorMsg);
    }

    // Получаем имя файла из заголовков, если сервер его прислал
    const cd = res.headers.get('Content-Disposition');
    let filename = fallbackName;
    if (cd && cd.includes('filename=')) {
      filename = cd.split('filename=')[1].replace(/["']/g, '');
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';
    
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 1000);
  }
};


// ==============================================================================
// БЛОК 3: API ДЛЯ ГЕНЕРАЦИИ ОТВЕТОВ ИИ (ОБЫЧНЫЙ РЕЖИМ)
// ==============================================================================

export const aiApi = {
  /**
   * Отправляет сообщение в чат и ждет полный ответ от LLM.
   * Используется, когда пользователь выключил стриминг (тумблер в интерфейсе).
   */
  askAi: (chatId: string, text: string, tags?: string[]) =>
    request<{ result: boolean; answer: string; message?: string }>(`/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST',
      body: JSON.stringify({ text, tags }),
    }),


// ==============================================================================
// БЛОК 4: API ДЛЯ ГЕНЕРАЦИИ ОТВЕТОВ ИИ (СТРИМИНГ / SSE)
// ==============================================================================

  /**
   * Отправляет сообщение и читает ответ в режиме реального времени (Server-Sent Events).
   * Используется, когда пользователь включил стриминг.
   * 
   * Вместо стандартного request() здесь используется fetch(), так как нам нужно 
   * читать поток байтов (ReadableStream) по мере его поступления.
   */
  askAiStream: async (
    chatId: string, 
    text: string, 
    tags: string[],
    onChunk: (chunk: string) => void,
    onError: (err: string) => void
  ) => {
    const token = getToken();
    
    // Принудительно включаем стриминг на бэкенде через query-параметр (force_stream=true)
    const response = await fetch(`${API_BASE}/ai/messages/stream?chat_id=${chatId}&force_stream=true`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ text, tags }),
    });

    // Обработка ошибок до начала стрима (например, 503 если vLLM выключен)
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      onError(data.message || `HTTP ${response.status}`);
      return;
    }

    if (!response.body) return;
    
    // Получаем "читатель" (Reader), который позволяет читать поток по кусочкам
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    // Бесконечный цикл чтения потока до его завершения
    while (true) {
      const { done, value } = await reader.read();
      if (done) break; // Сервер закончил генерацию

      // Декодируем пришедшие байты в строку и добавляем в буфер
      buffer += decoder.decode(value, { stream: true });
      
      // Бэкенд разделяет сообщения двойным переносом строки (\n\n)
      const lines = buffer.split('\n\n');
      
      // Последний элемент может быть незавершенным, оставляем его в буфере до следующего чанка
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          // Отрезаем префикс "data: "
          const dataStr = line.replace(/^data: /, '').trim();
          
          // Если бэкенд прислал маркер окончания
          if (dataStr === '[DONE]') return;
          
          try {
            const parsed = JSON.parse(dataStr);
            // Если пришел текст — отправляем в коллбэк для отрисовки
            if (parsed.text) onChunk(parsed.text);
            // Если пришла ошибка (например, обрыв соединения с vLLM посреди ответа)
            if (parsed.error) onError(parsed.error);
          } catch (e) {
            console.warn('Ошибка парсинга чанка:', dataStr);
          }
        }
      }
    }
  }
};