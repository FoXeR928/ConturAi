import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import { SlotProvider } from "./context/SlotEngine";
import { Layout } from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import ChatWindow from "./pages/ChatWindow";
import AdminDashboard from "./pages/AdminDashboard";

function ProtectedRoute({
  children,
  adminOnly = false,
}: {
  children: React.ReactNode;
  adminOnly?: boolean;
}) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
        Загрузка…
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && user.role !== "admin") return <Navigate to="/" replace />;
  return <>{children}</>;
}

function Shell() {
  const { user, loading } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={
          loading ? null : user ? <Navigate to="/" replace /> : <LoginPage />
        }
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<ChatWindow />} />
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute adminOnly>
                      <AdminDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <SlotProvider>
          <Shell />
        </SlotProvider>
      </AuthProvider>
    </ToastProvider>
  );
}