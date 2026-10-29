import { api } from './http';

export interface Chat {
  id: string;
  title: string;
  created_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
}

export const chatsApi = {
  list: (): Promise<Chat[]> => api('/chats'),

  create: (title: string): Promise<Chat> =>
    api('/chats', {
      method: 'POST',
      body: JSON.stringify({ title }),
    }),

  remove: (chatId: string): Promise<void> =>
    api(`/chats/${chatId}`, { method: 'DELETE' }),

  messages: (chatId: string): Promise<Message[]> =>
    api(`/chats/${chatId}/messages`),

  send: (
    chatId: string,
    pluginId: string,
    content: string,
  ): Promise<SendMessageResponse> =>
    api(`/chats/${chatId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ plugin_id: pluginId, content }),
    }),
};