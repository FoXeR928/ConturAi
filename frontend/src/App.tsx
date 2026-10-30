import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { authApi, MeResponse } from './api/auth';
import { LoginPage } from './pages/LoginPage';
import { ChatPage } from './pages/ChatPage';
import { PluginsPage } from './pages/PluginsPage';
import { UsersPage } from './pages/UsersPage';
import { ProfilePage } from './pages/ProfilePage';
import { ToastProvider } from './components/ToastProvider';

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
    <ToastProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        {!user && (
          <Route path="*" element={<Navigate to="/login" replace />} />
        )}
        {user && (
          <>
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            {isAdmin && (
              <Route path="/plugins" element={<PluginsPage />} />
            )}
            {isAdmin && (
              <Route path="/users" element={<UsersPage />} />
            )}
            <Route
              path="*"
              element={
                <Navigate to={isAdmin ? '/plugins' : '/chat'} replace />
              }
            />
          </>
        )}
      </Routes>
    </ToastProvider>
  );
}