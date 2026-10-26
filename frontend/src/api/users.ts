import { request } from './http';

export const usersApi = {
  getMe: () => request('/users/me'),
  getUsers: (includeDeleted = false) =>
    request(`/users/get?include_deleted=${includeDeleted}`),

  createUser: (login: string, user_name: string, password: string, role: string = 'user') =>
    request('/users/registration', {
      method: 'POST',
      body: JSON.stringify({ login, user_name, password, role }),
    }),

  updateUserStatus: (login: string, disabled: boolean) =>
    request('/users/change/status', {
      method: 'PATCH',
      body: JSON.stringify({ login, disabled }),
    }),

  updateUserRole: (login: string, role: string) =>
    request('/users/change/role', {
      method: 'PATCH',
      body: JSON.stringify({ login, role }),
    }),

  deleteUser: (login: string) =>
    request(`/users/delete?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),

  purgeUser: (login: string) =>
    request(`/users/purge?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),
};