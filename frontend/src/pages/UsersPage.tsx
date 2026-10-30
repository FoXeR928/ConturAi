import { FormEvent, useEffect, useState } from 'react';
import { usersApi, UserItem, UserRole } from '../api/users';
import { ApiError } from '../api/http';
import { useToast } from '../components/ToastProvider';

export function UsersPage() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [login, setLogin] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('user');
  const [creating, setCreating] = useState(false);
  const { show } = useToast();

  const load = async (): Promise<void> => {
    try {
      setUsers(await usersApi.list());
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка загрузки',
        'error',
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleCreate = async (event: FormEvent): Promise<void> => {
    event.preventDefault();
    setCreating(true);
    try {
      await usersApi.create({
        login,
        password,
        display_name: displayName || undefined,
        role,
      });
      show('Пользователь создан', 'success');
      setShowCreate(false);
      setLogin('');
      setDisplayName('');
      setPassword('');
      setRole('user');
      await load();
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка создания',
        'error',
      );
    } finally {
      setCreating(false);
    }
  };

  const updateRole = async (id: string, newRole: UserRole) => {
    try {
      const updated = await usersApi.updateRole(id, newRole);
      setUsers((prev) =>
        prev.map((u) => (u.id === id ? updated : u)),
      );
      show('Роль обновлена', 'success');
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка обновления',
        'error',
      );
    }
  };

  const toggleActive = async (user: UserItem) => {
    try {
      const updated = await usersApi.updateActive(
        user.id, !user.is_active,
      );
      setUsers((prev) =>
        prev.map((u) => (u.id === user.id ? updated : u)),
      );
      show(
        updated.is_active ? 'Пользователь активирован' : 'Пользователь заблокирован',
        'success',
      );
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка обновления',
        'error',
      );
    }
  };

  const resetPassword = async (user: UserItem) => {
    const newPassword = prompt(
      `Новый пароль для ${user.login} (мин. 6 символов):`,
    );
    if (!newPassword) return;
    try {
      await usersApi.updatePassword(user.id, newPassword);
      show('Пароль обновлён', 'success');
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка смены пароля',
        'error',
      );
    }
  };

  const removeUser = async (user: UserItem) => {
    if (!confirm(`Удалить пользователя "${user.login}"?`)) return;
    try {
      await usersApi.remove(user.id);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
      show('Пользователь удалён', 'success');
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка удаления',
        'error',
      );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              Пользователи
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Управление учётными записями и ролями.
            </p>
          </div>
          <button
            onClick={() => setShowCreate((v) => !v)}
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white
                       text-sm font-medium hover:bg-indigo-700"
          >
            {showCreate ? 'Отмена' : '+ Создать'}
          </button>
        </header>

        {showCreate && (
          <form
            onSubmit={handleCreate}
            className="bg-white rounded-lg border border-slate-200
                       shadow-sm p-6 space-y-4"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-600">
                  Логин
                </label>
                <input
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  required
                  minLength={3}
                  className="w-full px-3 py-2 rounded-lg border
                             border-slate-300 text-sm
                             focus:outline-none focus:ring-2
                             focus:ring-indigo-500"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-600">
                  Имя (опционально)
                </label>
                <input
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border
                             border-slate-300 text-sm
                             focus:outline-none focus:ring-2
                             focus:ring-indigo-500"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-600">
                  Пароль
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full px-3 py-2 rounded-lg border
                             border-slate-300 text-sm
                             focus:outline-none focus:ring-2
                             focus:ring-indigo-500"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-600">
                  Роль
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as UserRole)}
                  className="w-full px-3 py-2 rounded-lg border
                             border-slate-300 text-sm"
                >
                  <option value="user">user</option>
                  <option value="editor">editor</option>
                  <option value="admin">admin</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={creating}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white
                           text-sm font-medium hover:bg-indigo-700
                           disabled:opacity-60"
              >
                {creating ? 'Создание...' : 'Создать'}
              </button>
            </div>
          </form>
        )}

        {isLoading && (
          <p className="text-sm text-slate-500">Загрузка...</p>
        )}

        <div className="bg-white rounded-lg border border-slate-200
                        shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left border-b
                              border-slate-200">
              <tr>
                <th className="p-3">Логин</th>
                <th className="p-3">Имя</th>
                <th className="p-3">Роль</th>
                <th className="p-3">Статус</th>
                <th className="p-3 w-64">Действия</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr
                  key={u.id}
                  className="border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="p-3 font-mono text-xs">{u.login}</td>
                  <td className="p-3">{u.display_name || '—'}</td>
                  <td className="p-3">
                    <select
                      value={u.role}
                      onChange={(e) =>
                        updateRole(u.id, e.target.value as UserRole)
                      }
                      className="px-2 py-1 rounded border border-slate-300
                                 text-xs"
                    >
                      <option value="user">user</option>
                      <option value="editor">editor</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="p-3 text-xs">
                    <span
                      className={
                        'px-2 py-1 rounded ' +
                        (u.is_active
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-rose-100 text-rose-700')
                      }
                    >
                      {u.is_active ? 'активен' : 'заблокирован'}
                    </span>
                  </td>
                  <td className="p-3 space-x-2">
                    <button
                      onClick={() => toggleActive(u)}
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      {u.is_active ? 'Заблокировать' : 'Активировать'}
                    </button>
                    <button
                      onClick={() => resetPassword(u)}
                      className="text-xs text-indigo-600 hover:underline"
                    >
                      Пароль
                    </button>
                    <button
                      onClick={() => removeUser(u)}
                      className="text-xs text-rose-600 hover:underline"
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && !isLoading && (
                <tr>
                  <td
                    colSpan={5}
                    className="p-6 text-center text-slate-500"
                  >
                    Нет пользователей
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}