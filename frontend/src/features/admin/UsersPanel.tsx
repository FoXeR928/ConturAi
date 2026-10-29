import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { usersApi, UserItem } from '../../api/users';
import { useToast } from '../../components/ToastContext';

export function UsersPanel() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const { toast } = useToast();

  const load = async () => {
    try {
      const data = await usersApi.getUsers();
      setUsers(data.users || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Пользователи</h2>
      <div className="bg-white rounded-lg shadow overflow-hidden border border-gray-100">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left border-b">
            <tr>
              <th className="p-3">Логин</th>
              <th className="p-3">Имя</th>
              <th className="p-3">Роль</th>
              <th className="p-3">Статус</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.login} className="border-t hover:bg-gray-50">
                <td className="p-3 font-mono">{u.login}</td>
                <td className="p-3">{u.user_name || '—'}</td>
                <td className="p-3 text-xs">{u.role}</td>
                <td className="p-3 text-xs">
                  <span className={`px-2 py-1 rounded ${u.disabled ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {u.disabled ? 'заблокирован' : 'активен'}
                  </span>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={4} className="p-6 text-center text-gray-500">Нет пользователей</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}