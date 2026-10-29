import { request, getToken, API_BASE } from './http';

export interface Source {
  id: string;
  source: string;
  text: string;
  page: number;
}

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
  sources?: Source[];
}

export interface ChatsResponse {
  result: boolean;
  chats: Chat[];
}

export interface MessagesResponse {
  result: boolean;
  chat_name: string;
  messages_history: Message[];
  total_count: number;
}

export const chatsApi = {
  getChats: () => request<ChatsResponse>('/chats/get'),
  createChat: (name: string) => 
    request<{ result: boolean; chat_id: string }>('/chats/create', { method: 'POST', body: JSON.stringify({ name }) }),
  renameChat: (chatId: string, name: string) => 
    request(`/chats/rename?chat_id=${chatId}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  getMessages: (chatId: string, limit?: number, offset?: number) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const query = params.toString();
    return request<MessagesResponse>(`/chats/messages/get?chat_id=${chatId}${query ? `&${query}` : ''}`);
  },
  deleteMessage: (chatId: string, messageId: string) => 
    request(`/chats/messages/delete?chat_id=${chatId}&message_id=${messageId}`, { method: 'DELETE' }),
  softDeleteChat: (chatId: string) => 
    request(`/chats/delete?chat_id=${chatId}`, { method: 'PATCH' }),
  getDeletedChats: () => 
    request<ChatsResponse>('/chats/delete/irrevocably/get'),
  purgeDeletedChats: (chatIds: string[]) => 
    request('/chats/delete/irrevocably/list', { method: 'DELETE', body: JSON.stringify(chatIds) }),
  purgeAllDeletedChats: () => 
    request('/chats/delete/irrevocably/all', { method: 'DELETE' }),
  recoverChats: (chatIds: string[]) => 
    request('/chats/recovery/list', { method: 'PATCH', body: JSON.stringify(chatIds) }),
  exportChat: async (chatId: string, fallbackName: string) => {
    const token = getToken();
    const res = await fetch(`${API_BASE}/chats/export/${chatId}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) {
      let errorMsg = 'Не удалось скачать чат';
      try { const data = await res.json(); if (data.message) errorMsg = data.message; } catch (e) {}
      throw new Error(errorMsg);
    }
    const cd = res.headers.get('Content-Disposition');
    let filename = fallbackName;
    if (cd && cd.includes('filename=')) filename = cd.split('filename=')[1].replace(/["']/g, '');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.style.display = 'none';
    document.body.appendChild(a); a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 1000);
  }
};

export const aiApi = {
  askAi: (chatId: string, text: string, tags?: string[]) =>
    request<{ result: boolean; answer: string; sources: Source[]; message?: string }>(`/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST', body: JSON.stringify({ text, tags }),
    }),

  askAiStream: async (
    chatId: string, text: string, tags: string[],
    onSources: (sources: Source[]) => void, // <-- Новый коллбэк
    onChunk: (chunk: string) => void, 
    onError: (err: string) => void
  ) => {
    const token = getToken();
    const response = await fetch(`${API_BASE}/ai/messages/stream?chat_id=${chatId}&force_stream=true`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
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
            if (parsed.sources) onSources(parsed.sources);
            if (parsed.text) onChunk(parsed.text);
            if (parsed.error) onError(parsed.error);
          } catch (e) {}
        }
      }
    }
  }
};