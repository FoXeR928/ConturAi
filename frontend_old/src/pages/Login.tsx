import { useState, useEffect } from 'react';
import { Input } from '../ui/Input';
import { healthApi } from '../api/health'; 
import { ShieldCheck } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

interface LoginProps {
  onLogin: (login: string, password: string, rememberMe: boolean) => Promise<void>;
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function Login({ onLogin }: LoginProps) {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Состояние для хранения версии (получаем с бэкенда)
  const [version, setVersion] = useState('');

  // ==========================================================================
  // БЛОК 3: ЗАГРУЗКА ВЕРСИИ ПРИ СТАРТЕ
  // ==========================================================================
  
  useEffect(() => {
    healthApi.getStatus()
      .then(res => setVersion(res.version))
      .catch(() => setVersion('unknown'));
  }, []);

  // ==========================================================================
  // БЛОК 4: ОБРАБОТКА ОТПРАВКИ ФОРМЫ
  // ==========================================================================

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      await onLogin(login, password, rememberMe);
    } catch (err: any) {
      setError(err.message || 'Не удалось войти в систему');
      setLoading(false);
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
      <form 
        onSubmit={handleSubmit} 
        className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100"
      >
        <h2 className="text-3xl font-bold mb-2 text-center text-gray-900 tracking-tight">
          ConturAI
        </h2>
        <p className="text-center text-gray-500 text-sm mb-8">
          Войдите, чтобы продолжить работу
        </p>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-lg mb-6 text-sm flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-5">
          <div>
            <label htmlFor="login" className="block text-sm font-medium text-gray-700 mb-1.5">
              Логин
            </label>
            <Input
              id="login"
              type="text"
              autoFocus
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              disabled={loading}
              isInvalid={!!error}
              required
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
              Пароль
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              isInvalid={!!error}
              required
            />
          </div>
        </div>

        <div className="mt-4 flex items-center">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              disabled={loading}
              className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
            />
            <span className="text-sm text-gray-600 group-hover:text-gray-900 transition-colors flex items-center gap-1">
              <ShieldCheck size={14} className={rememberMe ? 'text-blue-500' : 'text-gray-400'} />
              Запомнить меня (на 7 дней)
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={loading || !login.trim() || !password.trim()}
          className="w-full mt-8 bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-500/30 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {loading ? 'Вход...' : 'Войти'}
        </button>

        {/* БЛОК ВЕРСИИ: Выводим версию в самом низу формы */}
        <div className="mt-8 text-center text-xs text-gray-400">
          ConturAI {version ? `v${version}` : '...'}
        </div>
      </form>
    </div>
  );
}