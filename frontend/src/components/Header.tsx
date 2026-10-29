import { Link, useLocation } from 'react-router-dom';
import { LogOut, MessageSquare, Shield } from 'lucide-react';
import { Button } from '../ui/Button';
import { ReactNode } from 'react';

export function Header({
  userName,
  isAdmin,
  onLogout,
  children, // <-- Для кнопок плагинов
}: {
  userName?: string;
  isAdmin: boolean;
  onLogout: () => void;
  children?: ReactNode;
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
    <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-gray-200 shrink-0">
      <div className="flex items-center gap-2">
        {tab('/chat', 'Чаты', MessageSquare)}
        {isAdmin && tab('/admin', 'Администрирование', Shield)}
      </div>
      
      <div className="flex items-center gap-4">
        {/* Слот для кнопок плагинов */}
        {children && <div className="flex items-center gap-2">{children}</div>}
        
        <span className="text-sm font-medium text-gray-700">{userName}</span>
        <Button variant="secondary" onClick={onLogout} className="flex gap-2 items-center py-1.5 px-3">
          <LogOut size={16} /> Выйти
        </Button>
      </div>
    </header>
  );
}