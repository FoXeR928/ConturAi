import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { Login } from './pages/Login';
import { ChatPage } from './pages/ChatPage';
import { AdminPage } from './pages/AdminPage';
import { NotFound } from './pages/NotFound';
import { login as authLogin, logout as authLogout } from './api/auth';
import { usersApi, UserRole } from './api/users';
import { ToastProvider } from './components/ToastContext';

interface Me {
  login: string;
  user_name?: string;
  role: UserRole;
  isAdmin: boolean;
}

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<Me | null>(null);
  const [initializing, setInitializing] = useState<boolean>(true);

  useEffect(() => {
    const restoreSession = async () => {
      if (!token) {
        setInitializing(false);
        return;
      }

      const stored = localStorage.getItem('me');
      if (stored) {
        try {
          setUser(JSON.parse(stored));
          setInitializing(false);
          return;
        } catch (e) {
          localStorage.removeItem('me');
        }
      }

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
        authLogout();
        setToken(null);
      } finally {
        setInitializing(false);
      }
    };

    restoreSession();
  }, [token]);

  const onLogin = async (login: string, password: string, rememberMe: boolean) => {
    const data = await authLogin(login, password, rememberMe);
    setToken(data.access_token);

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
  };

  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500 font-medium">Загрузка ConturAI...</div>
      </div>
    );
  }

  if (!token || !user) {
    return (
      <ToastProvider>
        <Login onLogin={onLogin} />
      </ToastProvider>
    );
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