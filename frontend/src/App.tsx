import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Login } from './pages/Login';
import { ChatPage } from './pages/ChatPage';
import { AdminPage } from './pages/AdminPage';
import { NotFound } from './pages/NotFound';
import { login as authLogin, logout as authLogout } from './api/auth';
import { usersApi } from './api/users';
import { ToastProvider } from './components/ToastContext';

interface Me {
  login: string;
  user_name?: string;
  role: string;
  isAdmin: boolean;
}

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<Me | null>(null);

  useEffect(() => {
    if (!token) return;
    const stored = localStorage.getItem('me');
    if (stored) setUser(JSON.parse(stored));
  }, [token]);

  const onLogin = async (login: string, password: string) => {
    // 1. Получаем токен
    const data = await authLogin(login, password);
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
      const me: Me = { login, role: 'user', isAdmin: false };
      localStorage.setItem('me', JSON.stringify(me));
      setUser(me);
    }
  };

  const onLogout = () => {
    authLogout();
    setToken(null);
    setUser(null);
    localStorage.removeItem('me'); 
  };

  if (!token || !user) {
    return <Login onLogin={onLogin} />;
  }

  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route
          path="/chat"
          element={<ChatPage userName={user.user_name || user.login} onLogout={onLogout} />}
        />
        {user.isAdmin && (
          <Route
            path="/admin"
            element={<AdminPage userName={user.user_name || user.login} onLogout={onLogout} />}
          />
        )}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </ToastProvider>
  );
}

export default App;