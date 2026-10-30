import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth';
import { ApiError } from '../api/http';

export function LoginPage() {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = await authApi.login({ login, password });
      navigate(me.role === 'admin' ? '/plugins' : '/chat');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Ошибка входа');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm bg-white rounded-lg
                   shadow-sm border border-slate-200 p-8 space-y-5"
      >
        <h1 className="text-xl font-semibold text-slate-900 text-center">
          ConturAI
        </h1>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700">Логин</label>
          <input
            type="text"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            required
            className="w-full px-3 py-2 rounded-lg border border-slate-300
                       text-sm focus:outline-none focus:ring-2
                       focus:ring-indigo-500"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700">Пароль</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-3 py-2 rounded-lg border border-slate-300
                       text-sm focus:outline-none focus:ring-2
                       focus:ring-indigo-500"
          />
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full py-2 rounded-lg bg-indigo-600 text-white
                     text-sm font-medium hover:bg-indigo-700
                     disabled:opacity-60 transition-colors"
        >
          {busy ? 'Вход...' : 'Войти'}
        </button>
      </form>
    </div>
  );
}