import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Login } from './pages/Login';
import { ChatPage } from './pages/ChatPage';
import { AdminPage } from './pages/AdminPage';
import { NotFound } from './pages/NotFound';
import { api } from './api/client';

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
    // 1. Получаем токен (если бэкенд упал, здесь вылетит понятная ошибка)
    const data = await api.login(login, password);
    setToken(data.access_token);

    // 2. Определяем, админ ли пользователь. 
    // Если getUsers вернет 403 (не админ) или 500 (ошибка БД) — мы просто
    // считаем его обычным пользователем и пускаем в чат.
    let me: Me = { login, isAdmin: false };
    try {
      const usersData = await api.getUsers();
      me = { login, isAdmin: true };
      
      // Пытаемся вытащить user_name для красоты
      const myRecord = usersData.users?.find((u: any) => u.login === login);
      if (myRecord && myRecord.user_name) {
        me.user_name = myRecord.user_name;
      }
    } catch {
      // Если 403 или другая ошибка — просто пускаем как обычного юзера
      me = { login, isAdmin: false };
    }
    
    localStorage.setItem('me', JSON.stringify(me));
    setUser(me);
  };

  const onLogout = () => {
    api.logout();
    localStorage.removeItem('me');
    setToken(null);
    setUser(null);
  };

  if (!token || !user) {
    return <Login onLogin={onLogin} />;
  }

  return (
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
  );
}

export default App;