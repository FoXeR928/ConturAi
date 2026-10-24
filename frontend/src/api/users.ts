import { request } from './http';

export const usersApi = {
  getUsers: (includeDeleted = false) =>
    request(`/users/get?include_deleted=${includeDeleted}`),

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
    request(`/users/delete?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),

  purgeUser: (login: string) =>
    request(`/users/purge?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),
};