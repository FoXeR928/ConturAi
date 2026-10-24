import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Modal } from '../../components/Modal';
import { usersApi } from '../../api/users';

interface UserRow {
  login: string;
  user_name: string;
  is_admin: boolean;
  disabled: boolean;
}

export function UsersPanel() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [showDeleted, setShowDeleted] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ login: '', user_name: '', password: '' });
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await usersApi.getUsers(showDeleted);
      setUsers(data.users || []);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, [showDeleted]);

  const create = async () => {
    try {
      await usersApi.createUser(form.login, form.user_name, form.password);
      setShowCreate(false);
      setForm({ login: '', user_name: '', password: '' });
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const toggleStatus = async (u: UserRow) => {
    try {
      await usersApi.updateUserStatus(u.login, !u.disabled);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const toggleRole = async (u: UserRow) => {
    try {
      await usersApi.updateUserRole(u.login, !u.is_admin);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const remove = async (u: UserRow) => {
    if (!confirm(`Удалить (в корзину) пользователя ${u.login}?`)) return;
    try {
      await usersApi.deleteUser(u.login);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const purge = async (u: UserRow) => {
    if (!confirm(`ВНИМАНИЕ! Пользователь ${u.login} и все его чаты будут удалены НАВСЕГДА. Продолжить?`)) return;
    try {
      await usersApi.purgeUser(u.login);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Пользователи</h2>
        <div className="flex gap-4 items-center">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
              className="w-4 h-4"
            />
            Показать удаленных
          </label>
          <Button onClick={() => setShowCreate(true)}>Создать</Button>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3">Логин</th>
              <th className="p-3">Имя</th>
              <th className="p-3">Роль</th>
              <th className="p-3">Статус</th>
              <th className="p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => {
              const isDeleted = u.login.includes('_deleted_');
              return (
                <tr key={u.login} className={`border-t ${isDeleted ? 'bg-gray-50 opacity-70' : ''}`}>
                  <td className="p-3 font-mono text-xs">{u.login}</td>
                  <td className="p-3">{u.user_name}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      u.is_admin ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {u.is_admin ? 'admin' : 'user'}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      u.disabled ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                    }`}>
                      {u.disabled ? 'заблокирован' : 'активен'}
                    </span>
                  </td>
                  <td className="p-3 space-x-2">
                    {!isDeleted ? (
                      <>
                        <button className="text-blue-600 hover:underline" onClick={() => toggleRole(u)}>
                          Роль
                        </button>
                        <button className="text-yellow-600 hover:underline" onClick={() => toggleStatus(u)}>
                          {u.disabled ? 'Разблокировать' : 'Заблокировать'}
                        </button>
                        <button className="text-red-600 hover:underline" onClick={() => remove(u)}>
                          Удалить
                        </button>
                      </>
                    ) : (
                      <button className="text-red-700 font-bold hover:underline" onClick={() => purge(u)}>
                        Удалить навсегда
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
            {users.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-gray-500">
                  Нет пользователей
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <Modal title="Создать пользователя" onClose={() => setShowCreate(false)}>
          <div className="space-y-3">
            <Input
              placeholder="Логин"
              value={form.login}
              onChange={(e) => setForm({ ...form, login: e.target.value })}
            />
            <Input
              placeholder="Имя"
              value={form.user_name}
              onChange={(e) => setForm({ ...form, user_name: e.target.value })}
            />
            <Input
              type="password"
              placeholder="Пароль"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
            <Button onClick={create} className="w-full">
              Создать
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}