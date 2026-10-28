import { request } from './http';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ (TYPESCRIPT INTERFACES)
// ==============================================================================

export type UserRole = 'user' | 'editor' | 'admin';

export interface UserItem {
  login: string;
  user_name: string;
  role: UserRole;
  disabled: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UsersResponse {
  result: boolean;
  users: UserItem[];
}

// ==============================================================================
// БЛОК 2: ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
// ==============================================================================

export const usersApi = {
  /**
   * Получить данные о текущем авторизованном пользователе.
   * 
   * Используется при перезагрузке страницы, чтобы понять:
   * - Кто вошел в систему (логин, отображаемое имя).
   * - Какую роль он имеет (чтобы показать или скрыть кнопку "Администрирование").
   */
  getMe: () => request('/users/me'),


// ==============================================================================
// БЛОК 3: ПРОСМОТР СПИСКА ПОЛЬЗОВАТЕЛЕЙ (АДМИН)
// ==============================================================================

  /**
   * Получить список всех пользователей.
   * 
   * @param includeDeleted - Если true, в список попадут и "удаленные" пользователи 
   * (те, у кого логин заканчивается на `_deleted_...`). Используется для корзины.
   */
  getUsers: (includeDeleted = false) =>
    request(`/users/get?include_deleted=${includeDeleted}`),


// ==============================================================================
// БЛОК 4: УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (АДМИН)
// ==============================================================================

  /**
   * Создать нового пользователя.
   * 
   * @param login - Уникальный логин (по нему будет вход).
   * @param user_name - Отображаемое имя (например, "Иванов И.И.").
   * @param password - Пароль в открытом виде (бэкенд зашифрует его через bcrypt).
   * @param role - Роль в системе: 'user', 'editor' или 'admin'.
   */
  createUser: (login: string, user_name: string, password: string, role: UserRole = 'user') =>
    request('/users/registration', {
      method: 'POST',
      body: JSON.stringify({ login, user_name, password, role }),
    }),

  /**
   * Заблокировать или разблокировать пользователя.
   * 
   * @param login - Логин пользователя, которого нужно заблокировать.
   * @param disabled - true (заблокирован) или false (активен).
   * 
   * ЗАЩИТА: Бэкенд запретит блокировать последнего администратора в системе.
   */
  updateUserStatus: (login: string, disabled: boolean) =>
    request('/users/change/status', {
      method: 'PATCH',
      body: JSON.stringify({ login, disabled }),
    }),

  /**
   * Изменить роль пользователя (например, повысить до админа или понизить).
   * 
   * @param login - Логин пользователя.
   * @param role - Новая роль ('user' | 'editor' | 'admin').
   * 
   * ЗАЩИТА: Бэкенд запретит понизить последнего администратора.
   */
  updateUserRole: (login: string, role: UserRole) =>
    request('/users/change/role', {
      method: 'PATCH',
      body: JSON.stringify({ login, role }),
    }),

  /**
   * Изменить отображаемое имя пользователя.
   */
  updateUserName: (login: string, user_name: string) =>
    request('/users/change/name', {
      method: 'PATCH',
      body: JSON.stringify({ login, user_name }),
    }),

  /**
   * Сменить пароль пользователя.
   * 
   * @param login - Логин пользователя.
   * @param password - Новый пароль.
   */
  updatePassword: (login: string, password: string) =>
    request('/users/change/password', {
      method: 'PATCH',
      body: JSON.stringify({ login, password }),
    }),


// ==============================================================================
// БЛОК 5: УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ (АДМИН)
// ==============================================================================

  /**
   * Мягкое удаление пользователя (перемещение в корзину).
   * 
   * Пользователь блокируется, а его логин переименовывается в `login_deleted_TIMESTAMP`.
   * Это позволяет сохранить историю чатов и сообщений, но освободить логин.
   */
  deleteUser: (login: string) =>
    request(`/users/delete?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),

  /**
   * Безвозвратное удаление пользователя из базы данных.
   * 
   * Удаляет запись пользователя и КАСКАДНО удаляет все его чаты и сообщения.
   * Обычно применяется к пользователям, которые уже находятся в корзине (`_deleted_`).
   */
  purgeUser: (login: string) =>
    request(`/users/purge?login=${encodeURIComponent(login)}`, {
      method: 'DELETE',
    }),
};