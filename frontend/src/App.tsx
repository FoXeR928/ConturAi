import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Login } from './pages/Login';
import { ChatPage } from './pages/ChatPage';
import { AdminPage } from './pages/AdminPage';
import { NotFound } from './pages/NotFound';
import { login as authLogin, logout as authLogout } from './api/auth';
import { usersApi, UserRole } from './api/users';
import { ToastProvider } from './components/ToastContext';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ
// ==============================================================================

interface Me {
  login: string;
  user_name?: string;
  role: UserRole;
  isAdmin: boolean; // Флаг для отображения ссылки на админку (доступна админам и редакторам)
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

function App() {
  // Состояния авторизации
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<Me | null>(null);
  
  // Флаг загрузки (чтобы не мигать формой логина при перезагрузке страницы)
  const [initializing, setInitializing] = useState<boolean>(true);

  // ==========================================================================
  // БЛОК 3: ВОССТАНОВЛЕНИЕ СЕССИИ ПРИ ЗАГРУЗКЕ
  // ==========================================================================

  useEffect(() => {
    const restoreSession = async () => {
      if (!token) {
        setInitializing(false);
        return;
      }

      // Пытаемся восстановить из localStorage
      const stored = localStorage.getItem('me');
      if (stored) {
        try {
          setUser(JSON.parse(stored));
          setInitializing(false);
          return;
        } catch (e) {
          // Если JSON битый — удаляем
          localStorage.removeItem('me');
        }
      }

      // Если токен есть, а данных нет — запрашиваем у сервера
      try {
        const meData = await usersApi.getMe();
        const me: Me = {
          login: meData.login,
          user_name: meData.user_name,
          role: meData.role,
          isAdmin: meData.role === 'admin' || meData.role === 'editor' 
        };
        localStorage.setItem('me', JSON.stringify(me));
        setUser(me);
      } catch (e) {
        // Если сервер вернул ошибку (токен истек), разлогиниваем
        authLogout();
        setToken(null);
      } finally {
        setInitializing(false);
      }
    };

    restoreSession();
  }, [token]);

  // ==========================================================================
  // БЛОК 4: ОБРАБОТКА ВХОДА И ВЫХОДА
  // ==========================================================================

  const onLogin = async (login: string, password: string, rememberMe: boolean) => {
    // 1. Получаем токен
    const data = await authLogin(login, password, rememberMe);
    setToken(data.access_token);

    // 2. Запрашиваем свою роль (эндпоинт /users/me)
    try {
      const meData = await usersApi.getMe();
      const me: Me = {
        login: meData.login,
        user_name: meData.user_name,
        role: meData.role,
        // Админка доступна и админам, и редакторам
        isAdmin: meData.role === 'admin' || meData.role === 'editor' 
      };
      localStorage.setItem('me', JSON.stringify(me));
      setUser(me);
    } catch (e) {
      console.error("Не удалось получить роль", e);
      // Если сервер не отдал роль, даем базовые права
      const me: Me = { login, role: 'user', isAdmin: false };
      localStorage.setItem('me', JSON.stringify(me));
      setUser(me);
    }
  };

  const onLogout = () => {
    authLogout(); // Очищает localStorage (токен и me)
    setToken(null);
    setUser(null);
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР
  // ==========================================================================

  // Пока проверяем токен — показываем экран загрузки (спиннер)
  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500 font-medium">Загрузка ConturAI...</div>
      </div>
    );
  }

  // Если нет токена или данных пользователя — показываем логин
  if (!token || !user) {
    return (
      <ToastProvider>
        <Login onLogin={onLogin} />
      </ToastProvider>
    );
  }

  // Если пользователь авторизован — показываем роуты
  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        
        <Route
          path="/chat"
          element={<ChatPage userName={user.user_name || user.login} onLogout={onLogout} />}
        />
        
        {/* Защищенный роут для админки */}
        {user.isAdmin && (
          <Route
            path="/admin"
            element={<AdminPage userName={user.user_name || user.login} onLogout={onLogout} />}
          />
        )}
        
        {/* 404 страница для всех остальных путей */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ToastProvider>
  );
}

export default App;