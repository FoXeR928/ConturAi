import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

export function Login({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password, remember);
      onLogin(); // Обновляем стейт в App.tsx
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">ConturAI Core</h2>
        {error && <div className="text-red-500 mb-4 text-sm bg-red-50 p-2 rounded">{error}</div>}
        <div className="space-y-4">
          <Input placeholder="Логин" value={username} onChange={e => setUsername(e.target.value)} />
          <Input type="password" placeholder="Пароль" value={password} onChange={e => setPassword(e.target.value)} />
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} />
            Запомнить меня
          </label>
          <Button type="submit" className="w-full">Войти</Button>
        </div>
      </form>
    </div>
  );
}