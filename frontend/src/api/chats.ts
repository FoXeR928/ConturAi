import { request, getToken } from './http';

export const chatsApi = {
  getChats: () => request('/chats/get'),
  createChat: (name: string) => request('/chats/create', { method: 'POST', body: JSON.stringify({ name }) }),
  getMessages: (chatId: string) => request(`/chats/messages/get?chat_id=${chatId}`),
  softDeleteChat: (chatId: string) => request(`/chats/delete?chat_id=${chatId}`, { method: 'PATCH' }),
  deleteMessage: (chatId: string, messageId: string) => request(`/chats/messages/delete?chat_id=${chatId}&message_id=${messageId}`, { method: 'DELETE' }),
  getDeletedChats: () => request('/chats/delete/irrevocably/get'),
  purgeDeletedChats: (chatIds: string[]) => request('/chats/delete/irrevocably/list', { method: 'DELETE', body: JSON.stringify(chatIds) }),
  purgeAllDeletedChats: () => request('/chats/delete/irrevocably/all', { method: 'DELETE' }),
  recoverChats: (chatIds: string[]) => request('/chats/recovery/list', { method: 'PATCH', body: JSON.stringify(chatIds) }),
};

export const aiApi = {
  askAi: (chatId: string, text: string, tags?: string[]) =>
    request(`/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST',
      body: JSON.stringify({ text, tags }),
    }),

  askAiStream: async (
    chatId: string, 
    text: string, 
    tags: string[],
    onChunk: (chunk: string) => void,
    onError: (err: string) => void
  ) => {
    const token = getToken();
    // force_stream=true заставляет бэкенд стримить, переопределяя настройку в БД
    const response = await fetch(`/api/ai/messages/stream?chat_id=${chatId}&force_stream=true`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ text, tags }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      onError(data.message || `HTTP ${response.status}`);
      return;
    }

    if (!response.body) return;
    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace(/^data: /, '').trim();
          if (dataStr === '[DONE]') return;
          
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.text) onChunk(parsed.text);
            if (parsed.error) onError(parsed.error);
          } catch (e) {
            console.warn('Ошибка парсинга чанка:', dataStr);
          }
        }
      }
    }
  }
};