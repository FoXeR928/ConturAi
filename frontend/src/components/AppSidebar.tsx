import { useLocation, Link } from 'react-router-dom';
import { MessageSquare, Shield, Plus, LogOut } from 'lucide-react';
import { Chat } from '../api/chats';

interface AppSidebarProps {
  userName: string;
  isAdmin: boolean;
  onLogout: () => void;
  
  // Для чатов
  chats: Chat[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onCreateChat: () => void;

  // Для админки
  adminTabs?: { id: string; label: string }[];
  activeAdminTab?: string;
  onSelectAdminTab?: (id: string) => void;
}

export function AppSidebar({
  userName,
  isAdmin,
  onLogout,
  chats,
  activeChatId,
  onSelectChat,
  onCreateChat,
  adminTabs = [],
  activeAdminTab,
  onSelectAdminTab,
}: AppSidebarProps) {
  const { pathname } = useLocation();
  const isAdminPage = pathname.startsWith('/admin');

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white select-none">
      {/* Шапка */}
      <div className="p-4 border-b border-gray-800">
        <h1 className="font-bold text-lg tracking-wide">ConturAI</h1>
        <div className="text-xs text-gray-400 mt-1">{userName}</div>
      </div>

      {/* Навигация (Чаты / Админка) */}
      <div className="p-2 space-y-1 border-b border-gray-800">
        <Link
          to="/chat"
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
            !isAdminPage ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'
          }`}
        >
          <MessageSquare size={16} /> Чаты
        </Link>
        {isAdmin && (
          <Link
            to="/admin"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isAdminPage ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800'
            }`}
          >
            <Shield size={16} /> Администрирование
          </Link>
        )}
      </div>

      {/* Динамический контент */}
      <div className="flex-1 overflow-y-auto p-2">
        {isAdminPage ? (
          /* --- МЕНЮ АДМИНКИ --- */
          <div className="space-y-1">
            {adminTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onSelectAdminTab?.(tab.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  activeAdminTab === tab.id
                    ? 'bg-gray-800 text-white font-medium'
                    : 'text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        ) : (
          /* --- СПИСОК ЧАТОВ --- */
          <div className="space-y-1">
            <button
              onClick={onCreateChat}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 mb-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
            >
              <Plus size={16} /> Новый чат
            </button>
            {chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`group flex items-center justify-between p-2.5 rounded-lg cursor-pointer text-sm transition-all ${
                  activeChatId === chat.id
                    ? 'bg-gray-800 text-white border-l-2 border-blue-500'
                    : 'text-gray-400 hover:bg-gray-800/60 hover:text-gray-200 border-l-2 border-transparent'
                }`}
              >
                <span className="truncate">{chat.name}</span>
              </div>
            ))}
            {chats.length === 0 && (
              <div className="text-center text-gray-500 text-xs mt-4">
                Нет чатов. Создайте новый!
              </div>
            )}
          </div>
        )}
      </div>

      {/* Кнопка выхода */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={onLogout}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <LogOut size={16} /> Выйти
        </button>
      </div>
    </div>
  );
}