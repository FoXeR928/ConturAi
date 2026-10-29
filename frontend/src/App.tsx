import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom'; // Убрали BrowserRouter
import { Login } from './pages/Login';
import { ChatPage } from './pages/ChatPage';
import { AdminPage } from './pages/AdminPage';
import { PluginProvider } from './plugins/PluginContext';
import { ToastProvider } from './components/ToastContext';
import { usersApi } from './api/users';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState<any>(null);
  const [init, setInit] = useState(true);

  useEffect(() => {
    if (!token) { 
      setInit(false); 
      return; 
    }
    
    usersApi.getMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('token');
        localStorage.removeItem('me');
        setToken(null);
      })
      .finally(() => setInit(false));
  }, [token]);

  if (init) {
    return <div className="h-screen flex items-center justify-center bg-gray-50">Загрузка...</div>;
  }

  return (
    <ToastProvider>
      <PluginProvider>
        <Routes>
          {/* Если токена нет — показываем только логин */}
          {!token ? (
            <Route path="*" element={<Login onLogin={() => setToken(localStorage.getItem('token'))} />} />
          ) : (
            <>
              <Route path="/chat" element={<ChatPage onLogout={() => { localStorage.clear(); setToken(null); setUser(null); }} />} />
              {(user?.role === 'admin' || user?.role === 'editor') && (
                <Route path="/admin" element={<AdminPage onLogout={() => { localStorage.clear(); setToken(null); setUser(null); }} />} />
              )}
              <Route path="*" element={<Navigate to="/chat" replace />} />
            </>
          )}
        </Routes>
      </PluginProvider>
    </ToastProvider>
  );
}