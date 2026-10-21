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
  const data = text ? JSON.parse(text) : {};
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
    if (!res.ok) throw new Error('Неверный логин или пароль');
    const data = await res.json();
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
  getMessages: (chatId: number) => request(`/chats/messages/get?chat_id=${chatId}`),
  askAi: (chatId: number, text: string) =>
    request(`/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  deleteChat: (chatId: number) => request(`/chats/delete?chat_id=${chatId}`, { method: 'PATCH' }),

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
  addDoc: (name: string, text: string) =>
    request('/ai/docs/create', {
      method: 'POST',
      body: JSON.stringify({ name, text }),
    }),
  readDoc: async (file: File) => {
    const fd = new FormData();
    fd.append('doc', file);
    return request('/ai/docs/read', { method: 'POST', body: fd });
  },
};