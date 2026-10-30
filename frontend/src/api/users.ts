import { api } from './http';

export type UserRole = 'user' | 'editor' | 'admin';

export interface UserItem {
  id: string;
  login: string;
  display_name: string | null;
  role: UserRole;
  is_active: boolean;
}

export const usersApi = {
  list: (): Promise<UserItem[]> => api('/users'),

  create: (payload: {
    login: string;
    password: string;
    display_name?: string;
    role: UserRole;
  }): Promise<UserItem> =>
    api('/users', { method: 'POST', body: JSON.stringify(payload) }),

  updateRole: (id: string, role: UserRole): Promise<UserItem> =>
    api(`/users/${id}/role`, {
      method: 'PATCH',
      body: JSON.stringify({ role }),
    }),

  updateActive: (id: string, is_active: boolean): Promise<UserItem> =>
    api(`/users/${id}/active`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active }),
    }),

  updatePassword: (id: string, password: string): Promise<void> =>
    api(`/users/${id}/password`, {
      method: 'PATCH',
      body: JSON.stringify({ password }),
    }),

  remove: (id: string): Promise<void> =>
    api(`/users/${id}`, { method: 'DELETE' }),
};