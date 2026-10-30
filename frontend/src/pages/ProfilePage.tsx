import { FormEvent, useState } from 'react';
import { authApi } from '../api/auth';
import { ApiError } from '../api/http';
import { useToast } from '../components/ToastProvider';

export function ProfilePage() {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [busy, setBusy] = useState(false);
  const { show } = useToast();

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (newPassword !== confirm) {
      show('Пароли не совпадают', 'error');
      return;
    }
    setBusy(true);
    try {
      await authApi.changeMyPassword(oldPassword, newPassword);
      show('Пароль обновлён', 'success');
      setOldPassword('');
      setNewPassword('');
      setConfirm('');
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка смены пароля',
        'error',
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-md mx-auto px-6 py-10 space-y-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">
            Профиль
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Смена пароля.
          </p>
        </header>

        <form
          onSubmit={onSubmit}
          className="bg-white rounded-lg border border-slate-200
                     shadow-sm p-6 space-y-4"
        >
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              Текущий пароль
            </label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg border border-slate-300
                         text-sm focus:outline-none focus:ring-2
                         focus:ring-indigo-500"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              Новый пароль
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              className="w-full px-3 py-2 rounded-lg border border-slate-300
                         text-sm focus:outline-none focus:ring-2
                         focus:ring-indigo-500"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-slate-700">
              Повторите новый пароль
            </label>
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              minLength={6}
              className="w-full px-3 py-2 rounded-lg border border-slate-300
                         text-sm focus:outline-none focus:ring-2
                         focus:ring-indigo-500"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={busy}
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white
                         text-sm font-medium hover:bg-indigo-700
                         disabled:opacity-60"
            >
              {busy ? 'Сохранение...' : 'Сменить пароль'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}