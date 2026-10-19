const API_BASE = '/api';

export const api = {
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    if (!res.ok) throw new Error('Неверный логин или пароль');
    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    return data;
  },
  async getChats() {
    const res = await fetch(`${API_BASE}/chats/get`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    });
    return res.json();
  },
  async createChat(name: string) {
    const res = await fetch(`${API_BASE}/chats/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: JSON.stringify({ name })
    });
    return res.json();
  },
  async getMessages(chatId: number) {
    const res = await fetch(`${API_BASE}/chats/messages/get?chat_id=${chatId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    });
    return res.json();
  },
  async askAi(chatId: number, text: string) {
    const res = await fetch(`${API_BASE}/ai/messages/create?chat_id=${chatId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
      body: JSON.stringify({ text })
    });
    return res.json();
  }
};