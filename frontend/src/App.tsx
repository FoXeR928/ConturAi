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

    // 2. Определяем, админ ли пользователь
    let me: Me = { login, isAdmin: false };
    try {
      const usersData = await usersApi.getUsers();
      me = { login, isAdmin: true };

      const myRecord = usersData.users?.find((u: any) => u.login === login);
      if (myRecord && myRecord.user_name) {
        me.user_name = myRecord.user_name;
      }
    } catch {
      me = { login, isAdmin: false };
    }

    localStorage.setItem('me', JSON.stringify(me));
    setUser(me);
  };

  const onLogout = () => {
    authLogout();
    setToken(null);
    setUser(null);
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