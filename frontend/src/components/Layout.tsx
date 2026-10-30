import { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();

  const isActive = (path: string) =>
    loc.pathname === path ? "text-brand-400" : "text-slate-400 hover:text-slate-200";

  const handleLogout = () => {
    logout();
    nav("/login", { replace: true });
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center font-bold text-white">
                C
              </div>
              <span className="text-base font-semibold tracking-tight">
                Contur<span className="text-brand-400">AI</span>
              </span>
            </Link>
            <nav className="hidden md:flex items-center gap-5 text-sm">
              <Link to="/" className={isActive("/")}>
                Чат
              </Link>
              {user?.role === "admin" && (
                <Link to="/admin" className={isActive("/admin")}>
                  Администрирование
                </Link>
              )}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {user && (
              <>
                <div className="text-right hidden sm:block">
                  <div className="text-xs text-slate-400">Вы вошли как</div>
                  <div className="text-sm text-slate-200 font-medium">
                    {user.username}{" "}
                    {user.role === "admin" && (
                      <span className="text-xs text-brand-400 ml-1">· admin</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg"
                >
                  Выйти
                </button>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col">{children}</main>
    </div>
  );
}