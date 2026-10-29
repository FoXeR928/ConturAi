import { request } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

export type UserRole = 'user' | 'editor' | 'admin';

export interface UserItem {
  login: string;
  user_name: string;
  role: UserRole;
  disabled: boolean;
  created_at?: string;
}

export interface UsersResponse {
  result: boolean;
  users: UserItem[];
}

// ==============================================================================
// БЛОК 2: API ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ
// ==============================================================================

export const usersApi = {
  /** Получить данные о текущем авторизованном пользователе */
  getMe: () => request<{ login: string; user_name: string; role: UserRole }>('/users/me'),

  /** Получить список всех пользователей (доступно только админу) */
  getUsers: (includeDeleted = false) => 
    request<UsersResponse>(`/users/get?include_deleted=${includeDeleted}`),

  /** Создать нового пользователя */
  createUser: (login: string, user_name: string, password: string, role: UserRole = 'user') =>
    request('/users/registration', {
      method: 'POST',
      body: JSON.stringify({ login, user_name, password, role }),
    }),

  /** Изменить роль пользователя */
  updateUserRole: (login: string, role: UserRole) =>
    request('/users/change/role', {
      method: 'PATCH',
      body: JSON.stringify({ login, role }),
    }),

  /** Заблокировать или разблокировать пользователя */
  updateUserStatus: (login: string, disabled: boolean) =>
    request('/users/change/status', {
      method: 'PATCH',
      body: JSON.stringify({ login, disabled }),
    }),

  /** Изменить отображаемое имя */
  updateUserName: (login: string, user_name: string) =>
    request('/users/change/name', {
      method: 'PATCH',
      body: JSON.stringify({ login, user_name }),
    }),

  /** Сменить пароль */
  updatePassword: (login: string, password: string) =>
    request('/users/change/password', {
      method: 'PATCH',
      body: JSON.stringify({ login, password }),
    }),

  /** Мягкое удаление пользователя (в корзину) */
  deleteUser: (login: string) =>
    request(`/users/delete?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),

  /** Безвозвратное удаление пользователя */
  purgeUser: (login: string) =>
    request(`/users/purge?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),
};