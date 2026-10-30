import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button, FormField, Input } from "../components/shared/DesignSystem";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      nav("/", { replace: true });
    } catch (err) {
      setError((err as Error).message || "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white mx-auto mb-4">
            C
          </div>
          <h1 className="text-2xl font-semibold">
            Contur<span className="text-brand-400">AI</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">Вход в систему</p>
        </div>

        <form
          onSubmit={submit}
          className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4"
        >
          <FormField label="Имя пользователя" required>
            <Input
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </FormField>
          <FormField label="Пароль" required>
            <Input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </FormField>

          {error && (
            <div className="text-xs text-red-300 bg-red-950/50 border border-red-800 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <Button type="submit" loading={loading} className="w-full" size="md">
            Войти
          </Button>
        </form>

        <p className="text-xs text-center text-slate-500 mt-4">
          По умолчанию: <code className="text-slate-400">admin / admin123</code>
        </p>
      </div>
    </div>
  );
}