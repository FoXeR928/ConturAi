import { request } from './http';

export interface Chat { id: string; name: string; created_at: string; }
export interface Message { id: string; chat_role: 'user'|'assistant'; text: string; created_at: string; }

export const chatsApi = {
  getChats: () => request<{ chats: Chat[] }>('/chats/get'),
  createChat: (name: string) => request<{ chat_id: string }>('/chats/create', { method: 'POST', body: JSON.stringify({ name }) }),
  getMessages: (chatId: string) => request<{ chat_name: string, messages_history: Message[], total: number }>(`/chats/messages/get?chat_id=${chatId}`),
  
  // ДОБАВЛЕНО: отправка сообщения
  createMessage: (chatId: string, text: string) => 
    request(`/chats/messages/create?chat_id=${chatId}`, { 
      method: 'POST', 
      body: JSON.stringify({ text }) 
    }),
};