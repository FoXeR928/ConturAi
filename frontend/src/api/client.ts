const API_BASE = '/api';

async function request(path: string, opts: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(opts.body instanceof FormData) && opts.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  const text = await res.text();
  let data: any = {};
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = {
        result: false,
        message: `Ошибка сервера: HTTP ${res.status} ${res.statusText}`,
        category: 'error',
      };
    }
  }
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    throw new Error(data.message || `HTTP ${res.status}`);
  }
  return data;
}

export const api = {
  // --- auth ---
  async login(username: string, password: string) {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });

    // Читаем ответ как текст, чтобы перехватить ошибки 500/502
    const text = await res.text();
    let data: any = {};
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = { message: `Ошибка сервера: HTTP ${res.status}` };
      }
    }

    if (!res.ok) {
      // Показываем сообщение от бэкенда, если оно есть
      throw new Error(data.message || `Ошибка входа: HTTP ${res.status}`);
    }

    if (!data.access_token) {
      throw new Error('Сервер не вернул токен авторизации');
    }

    localStorage.setItem('token', data.access_token);
    return data;
  },
  logout() {
    localStorage.removeItem('token');
  },

  // --- chats ---
  getChats: () => request('/chats/get'),
  createChat: (name: string) =>
    request('/chats/create', { method: 'POST', body: JSON.stringify({ name }) }),
  getMessages: (chatId: string) => request(`/chats/messages/get?chat_id=${chatId}`),
  askAi: (chatId: string, text: string) =>
    request(`/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  deleteChat: (chatId: string) =>
    request(`/chats/delete?chat_id=${chatId}`, { method: 'PATCH' }),

  // --- users (admin) ---
  getUsers: () => request('/users/get'),
  createUser: (login: string, user_name: string, password: string) =>
    request('/users/registration', {
      method: 'POST',
      body: JSON.stringify({ login, user_name, password }),
    }),
  updateUserStatus: (login: string, disabled: boolean) =>
    request('/users/change/status', {
      method: 'PATCH',
      body: JSON.stringify({ login, disabled }),
    }),
  updateUserRole: (login: string, is_admin: boolean) =>
    request('/users/change/role', {
      method: 'PATCH',
      body: JSON.stringify({ login, is_admin }),
    }),
  deleteUser: (login: string) =>
    request(`/users/delete?login=${encodeURIComponent(login)}`, { method: 'DELETE' }),

  // --- prompts (admin) ---
  getPrompts: () => request('/prompts/get'),
  updatePrompt: (key: string, value: string) =>
    request('/prompts/update', { method: 'PATCH', body: JSON.stringify({ key, value }) }),

  // --- llm configs (admin) ---
  getLlmConfigs: () => request('/llm-configs/get'),
  updateLlmConfig: (key: string, value: string) =>
    request('/llm-configs/update', {
      method: 'PATCH',
      body: JSON.stringify({ key, value }),
    }),

  // --- docs (admin) ---
  listDocs: () => request('/ai/docs/list'),

  readDoc: async (file: File) => {
    const fd = new FormData();
    fd.append('doc', file);
    return request('/ai/docs/read', { method: 'POST', body: fd });
  },

  addDoc: (name: string, text: string, uploadId?: string) =>
    request('/ai/docs/create', {
      method: 'POST',
      body: JSON.stringify({ name, text, upload_id: uploadId }),
    }),

  downloadDoc: async (uploadId: string, fileName: string) => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}/ai/docs/${uploadId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  deleteDoc: (uploadId: string) =>
    request(`/ai/docs/${uploadId}`, { method: 'DELETE' }),
};