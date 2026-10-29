import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { authApi, MeResponse } from './api/auth';
import { LoginPage } from './pages/LoginPage';
import { ChatPage } from './pages/ChatPage';
import { PluginsPage } from './pages/PluginsPage';

export default function App() {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!authApi.isAuthenticated()) {
      setReady(true);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => authApi.logout())
      .finally(() => setReady(true));
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center
                      text-slate-400">
        ...
      </div>
    );
  }

  const isAdmin = user?.role === 'admin';

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {!user && (
        <Route path="*" element={<Navigate to="/login" replace />} />
      )}
      {user && (
        <>
          <Route path="/chat" element={<ChatPage />} />
          {isAdmin && (
            <Route path="/plugins" element={<PluginsPage />} />
          )}
          <Route
            path="*"
            element={
              <Navigate
                to={isAdmin ? '/plugins' : '/chat'}
                replace
              />
            }
          />
        </>
      )}
    </Routes>
  );
}