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