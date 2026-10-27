import { useState } from 'react';
import { Input } from '../../ui/Input';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

interface LoginProps {
  /** 
   * Функция, которая вызывается при отправке формы.
   * Должна возвращать Promise. Если Promise отклонен (throw), 
   * мы перехватим ошибку и покажем её пользователю.
   */
  onLogin: (login: string, password: string) => Promise<void>;
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function Login({ onLogin }: LoginProps) {
  // Поля формы
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  
  // Состояния интерфейса
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // ==========================================================================
  // БЛОК 3: ОБРАБОТКА ОТПРАВКИ ФОРМЫ
  // ==========================================================================

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Отменяем стандартную перезагрузку страницы
    
    setError('');
    setLoading(true);
    
    try {
      // Вызываем функцию из App.tsx (которая делает запрос к бэкенду)
      await onLogin(login, password);
      // Если успешно — App.tsx сам перекинет пользователя в чат (изменит стейт token)
    } catch (err: any) {
      // Если сервер вернул ошибку (401, 500), показываем красную плашку
      setError(err.message || 'Не удалось войти в систему');
      setLoading(false);
    }
  };

  // ==========================================================================
  // БЛОК 4: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <form 
        onSubmit={handleSubmit} 
        className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-gray-100"
      >
        {/* Логотип и заголовок */}
        <h2 className="text-3xl font-bold mb-2 text-center text-gray-900 tracking-tight">
          ConturAI
        </h2>
        <p className="text-center text-gray-500 text-sm mb-8">
          Войдите, чтобы продолжить работу
        </p>

        {/* Блок ошибок */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-lg mb-6 text-sm flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Поля ввода */}
        <div className="space-y-5">
          <div>
            <label htmlFor="login" className="block text-sm font-medium text-gray-700 mb-1.5">
              Логин
            </label>
            <input
              id="login"
              type="text"
              autoFocus // Автофокус при открытии страницы
              className="w-full border border-gray-300 rounded-lg p-2.5 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:bg-gray-100"
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
            <input
              id="password"
              type="password"
              className="w-full border border-gray-300 rounded-lg p-2.5 text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:bg-gray-100"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              isInvalid={!!error}
              required
            />
          </div>
        </div>

        {/* Кнопка отправки */}
        <button
          type="submit"
          disabled={loading || !login.trim() || !password.trim()}
          className="w-full mt-8 bg-blue-600 text-white py-2.5 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-500/30 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {loading ? 'Вход...' : 'Войти'}
        </button>
      </form>
    </div>
  );
}