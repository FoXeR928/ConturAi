import { api, getToken, ApiError } from './http';

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

export interface StreamDone {
  done: true;
  assistant_message_id: number;
}

export interface StreamCallbacks {
  onDelta: (delta: string) => void;
  onDone: (info: StreamDone) => void;
  onError: (error: string) => void;
}

const API_BASE = '/api/v1';

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

  async sendStream(
    chatId: string,
    pluginId: string,
    content: string,
    callbacks: StreamCallbacks,
    signal: AbortSignal,
  ): Promise<void> {
    const token = getToken();
    const headers = new Headers({ 'Content-Type': 'application/json' });
    if (token) headers.set('Authorization', `Bearer ${token}`);

    const response = await fetch(
      `${API_BASE}/chats/${chatId}/messages/stream`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify({ plugin_id: pluginId, content }),
        signal,
      },
    );
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const message =
        body?.error?.message ?? `HTTP ${response.status}`;
      throw new ApiError('STREAM_ERROR', message, response.status);
    }
    if (!response.body) {
      callbacks.onError('Ответ без тела');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let boundary = buffer.indexOf('\n\n');
      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf('\n\n');
        if (!chunk.startsWith('data: ')) continue;
        const raw = chunk.slice(6);
        if (raw === '[DONE]') return;
        try {
          const obj = JSON.parse(raw);
          if (obj.delta) callbacks.onDelta(obj.delta as string);
          else if (obj.done) {
            callbacks.onDone({
              done: true,
              assistant_message_id: obj.assistant_message_id,
            });
          } else if (obj.error) callbacks.onError(obj.error as string);
        } catch {
          // игнорируем нераспарсенное
        }
      }
    }
  },
};