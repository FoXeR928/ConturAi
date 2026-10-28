import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Modal } from '../../components/Modal';
import { usersApi, UserItem, UserRole } from '../../api/users';
import { useToast } from '../../components/ToastContext';
import { RefreshCw, UserPlus, ShieldAlert, CheckCircle, XCircle } from 'lucide-react';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function UsersPanel() {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [showDeleted, setShowDeleted] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  
  // Состояния для формы создания
  const [form, setForm] = useState({ login: '', user_name: '', password: '', role: 'user' as UserRole });
  
  // Состояния загрузки
  const [createLoading, setCreateLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null); // Хранит логин юзера, с которым сейчас идет действие
  
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
const [editForm, setEditForm] = useState({ user_name: '', password: '' });

  const { toast } = useToast();

  // ==========================================================================
  // БЛОК 2: ЗАГРУЗКА ДАННЫХ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await usersApi.getUsers(showDeleted);
      setUsers(data.users || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => {
    load();
  }, [showDeleted]);

  // ==========================================================================
  // БЛОК 3: ДЕЙСТВИЯ С ПОЛЬЗОВАТЕЛЯМИ
  // ==========================================================================

  const create = async () => {
    if (!form.login.trim() || !form.password.trim()) {
      toast('Логин и пароль обязательны', 'error');
      return;
    }

    setCreateLoading(true);
    try {
      await usersApi.createUser(form.login, form.user_name, form.password, form.role);
      toast('Пользователь успешно создан', 'success');
      
      // Очищаем форму и закрываем модалку
      setShowCreate(false);
      setForm({ login: '', user_name: '', password: '', role: 'user' });
      
      await load(); // Обновляем список
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setCreateLoading(false);
    }
  };

  const toggleStatus = async (u: UserItem) => {
    setActionLoading(u.login);
    try {
      await usersApi.updateUserStatus(u.login, !u.disabled);
      toast(u.disabled ? 'Пользователь разблокирован' : 'Пользователь заблокирован', 'success');
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const updateRole = async (login: string, newRole: string) => {
    setActionLoading(login);
    try {
      await usersApi.updateUserRole(login, newRole as UserRole);
      toast(`Роль изменена на "${newRole}"`, 'success');
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
      await load(); // Откатываем селект обратно, если сервер вернул ошибку (например, последний админ)
    } finally {
      setActionLoading(null);
    }
  };

  const remove = async (u: UserItem) => {
    if (!confirm(`Отправить пользователя ${u.login} в корзину? Он больше не сможет войти.`)) return;
    
    setActionLoading(u.login);
    try {
      await usersApi.deleteUser(u.login);
      toast('Пользователь перемещен в корзину', 'success');
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const purge = async (u: UserItem) => {
    if (!confirm(`ВНИМАНИЕ! Пользователь ${u.login} и все его чаты будут удалены НАВСЕГДА. Продолжить?`)) return;
    
    setActionLoading(u.login);
    try {
      await usersApi.purgeUser(u.login);
      toast('Пользователь удален навсегда', 'success');
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditClick = (u: UserItem) => {
  setEditingUser(u);
  setEditForm({ user_name: u.user_name || '', password: '' });
};

const saveProfile = async () => {
  if (!editingUser) return;
  setActionLoading(editingUser.login);
  try {
    // Меняем имя, если оно изменилось
    if (editForm.user_name !== editingUser.user_name) {
      await usersApi.updateUserName(editingUser.login, editForm.user_name);
    }
    // Меняем пароль, если он введен
    if (editForm.password.trim()) {
      await usersApi.updatePassword(editingUser.login, editForm.password);
    }
    toast('Данные пользователя обновлены', 'success');
    setEditingUser(null);
    await load();
  } catch (e: any) {
    toast(e.message, 'error');
  } finally {
    setActionLoading(null);
  }
};

  // ==========================================================================
  // БЛОК 4: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      {/* Шапка */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <UserPlus size={24} className="text-blue-600" /> Пользователи
        </h2>
        
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Показать удаленных
          </label>
          
          <Button onClick={() => setShowCreate(true)} className="flex items-center gap-2">
            <UserPlus size={16} /> Создать
          </Button>
        </div>
      </div>

      {/* Таблица с горизонтальным скроллом для мобильных */}
      <div className="bg-white rounded-lg shadow overflow-hidden border border-gray-100">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[700px]">
            <thead className="bg-gray-50 text-left border-b">
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
                const isBusy = actionLoading === u.login;

                return (
                  <tr key={u.login} className={`border-t transition-colors ${isDeleted ? 'bg-gray-50 opacity-75' : 'hover:bg-gray-50'}`}>
                    <td className="p-3 font-mono text-xs font-semibold text-gray-700">{u.login}</td>
                    
                    <td className="p-3 text-gray-800">{u.user_name || '—'}</td>
                    
                    {/* Выбор роли */}
                    <td className="p-3">
                      <select
                        value={u.role || 'user'}
                        onChange={(e) => updateRole(u.login, e.target.value)}
                        disabled={isDeleted || isBusy}
                        className={`border rounded-lg p-1.5 text-xs font-medium focus:ring-2 focus:ring-blue-500 outline-none ${
                          u.role === 'admin' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                          u.role === 'editor' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                          'bg-white text-gray-700 border-gray-300'
                        }`}
                      >
                        <option value="user">user</option>
                        <option value="editor">editor</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    
                    {/* Статус */}
                    <td className="p-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium inline-flex items-center gap-1 ${
                        u.disabled ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                      }`}>
                        {u.disabled ? <XCircle size={12}/> : <CheckCircle size={12}/>}
                        {u.disabled ? 'заблокирован' : 'активен'}
                      </span>
                    </td>
                    
                    {/* Действия */}
                    <td className="p-3 space-x-3">
                      {isBusy ? (
                        <span className="text-gray-400 text-xs inline-flex items-center gap-1">
                          <RefreshCw size={14} className="animate-spin" /> Обработка...
                        </span>
                      ) : !isDeleted ? (
                        <>
                          <button onClick={() => handleEditClick(u)} className="text-blue-600 hover:underline text-xs font-medium">
                            Изменить
                          </button>
                          <button className="text-yellow-600 hover:underline text-xs font-medium" onClick={() => toggleStatus(u)}>
                            {u.disabled ? 'Разблокировать' : 'Заблокировать'}
                          </button>
                          <button 
                            className="text-red-600 hover:text-red-800 hover:underline text-xs font-medium" 
                            onClick={() => remove(u)}
                          >
                            Удалить
                          </button>
                        </>
                      ) : (
                        <button 
                          className="text-red-700 bg-red-50 px-2 py-1 rounded hover:bg-red-100 font-bold text-xs inline-flex items-center gap-1 transition-colors" 
                          onClick={() => purge(u)}
                        >
                          <ShieldAlert size={14} /> Удалить навсегда
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
              
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    Нет пользователей для отображения.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ======================================================================
          МОДАЛЬНОЕ ОКНО СОЗДАНИЯ
          ====================================================================== */}
      {showCreate && (
        <Modal title="Создать пользователя" onClose={() => !createLoading && setShowCreate(false)}>
          <div className="space-y-4">
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Логин *</label>
              <Input
                placeholder="Например: ivanov"
                value={form.login}
                onChange={(e) => setForm({ ...form, login: e.target.value })}
                disabled={createLoading}
                isInvalid={form.login.length > 0 && form.login.length < 3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Отображаемое имя</label>
              <Input
                placeholder="Например: Иванов И.И."
                value={form.user_name}
                onChange={(e) => setForm({ ...form, user_name: e.target.value })}
                disabled={createLoading}
                isInvalid={form.login.length > 0 && form.login.length < 3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Пароль *</label>
              <Input
                type="password"
                placeholder="Минимум 8 символов"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                disabled={createLoading}
                isInvalid={form.login.length > 0 && form.login.length < 3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Роль в системе</label>
              <select
                className="w-full border rounded-lg p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
                disabled={createLoading}
              >
                <option value="user">Пользователь (user) — только чаты</option>
                <option value="editor">Редактор (editor) — загрузка документов</option>
                <option value="admin">Администратор (admin) — полный доступ</option>
              </select>
            </div>

            <div className="pt-2">
              <Button 
                onClick={create} 
                disabled={createLoading || !form.login.trim() || !form.password.trim()} 
                className="w-full flex justify-center"
              >
                {createLoading ? <RefreshCw size={18} className="animate-spin" /> : 'Создать пользователя'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}