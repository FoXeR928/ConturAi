import { request } from './http';

export const chatsApi = {
  getChats: () => request('/chats/get'),

  createChat: (name: string) =>
    request('/chats/create', { method: 'POST', body: JSON.stringify({ name }) }),

  getMessages: (chatId: string) =>
    request(`/chats/messages/get?chat_id=${chatId}`),

  softDeleteChat: (chatId: string) =>
    request(`/chats/delete?chat_id=${chatId}`, { method: 'PATCH' }),

  deleteMessage: (chatId: string, messageId: string) =>
    request(
      `/chats/messages/delete?chat_id=${chatId}&message_id=${messageId}`,
      { method: 'DELETE' }
    ),

  // Корзина (admin)
  getDeletedChats: () => request('/chats/delete/irrevocably/get'),

  purgeDeletedChats: (chatIds: string[]) =>
    request('/chats/delete/irrevocably/list', {
      method: 'DELETE',
      body: JSON.stringify(chatIds),
    }),

  purgeAllDeletedChats: () =>
    request('/chats/delete/irrevocably/all', { method: 'DELETE' }),

  recoverChats: (chatIds: string[]) =>
    request('/chats/recovery/list', {
      method: 'PATCH',
      body: JSON.stringify(chatIds),
    }),
  
};

export const aiApi = {
  askAi: (chatId: string, text: string) =>
    request(`/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
};

export const streamAiMessage = async (
  chatId: string,
  text: string,
  onChunk: (chunk: string) => void,
  onDone: () => void
) => {
  const token = localStorage.getItem('token');
  const res = await fetch(`/ai/messages/stream?chat_id=${chatId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ text }),
  });

  if (!res.ok || !res.body) throw new Error('Ошибка стриминга');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || ''; // Оставляем недописанную часть

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const dataStr = line.replace('data: ', '');
        if (dataStr === '[DONE]') {
          onDone();
          return;
        }
        try {
          const data = JSON.parse(dataStr);
          if (data.text) onChunk(data.text);
          if (data.error) throw new Error(data.error);
        } catch (e) {
          console.error('SSE Parse error', e);
        }
      }
    }
  }
};