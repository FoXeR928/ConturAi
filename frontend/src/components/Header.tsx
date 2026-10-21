import { Link, useLocation } from 'react-router-dom';
import { LogOut, MessageSquare, Shield } from 'lucide-react';
import { Button } from '../ui/Button';

export function Header({
  userName,
  isAdmin,
  onLogout,
}: {
  userName?: string;
  isAdmin: boolean;
  onLogout: () => void;
}) {
  const { pathname } = useLocation();
  const tab = (to: string, label: string, Icon: any) => (
    <Link
      to={to}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        pathname.startsWith(to)
          ? 'bg-blue-600 text-white'
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      <Icon size={16} />
      {label}
    </Link>
  );

  return (
    <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-gray-200">
      <div className="flex items-center gap-2">
        {tab('/chat', 'Чаты', MessageSquare)}
        {isAdmin && tab('/admin', 'Администрирование', Shield)}
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{userName}</span>
        <Button variant="secondary" onClick={onLogout} className="flex gap-2 items-center">
          <LogOut size={16} /> Выйти
        </Button>
      </div>
    </header>
  );
}