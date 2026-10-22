import { LogOut, Plus, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../ui/Button';

interface SidebarProps {
  chats: any[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onCreateChat: () => void;
  onLogout: () => void;
  isAdmin?: boolean;
}

export function Sidebar({
  chats,
  activeChatId,
  onSelectChat,
  onCreateChat,
  onLogout,
  isAdmin,
}: SidebarProps) {
  return (
    <>
      <div className="p-4 border-b border-gray-800 flex justify-between items-center">
        <h1 className="font-bold text-lg">ConturAI</h1>
        <button onClick={onLogout} className="text-gray-400 hover:text-white">
          <LogOut size={20} />
        </button>
      </div>
      <div className="p-4 space-y-2">
        <Button onClick={onCreateChat} className="w-full flex justify-center gap-2">
          <Plus size={18} /> Новый чат
        </Button>
        {isAdmin && (
          <Link
            to="/admin"
            className="flex items-center gap-2 justify-center w-full px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm"
          >
            <Shield size={16} /> Администрирование
          </Link>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {chats.map((chat) => (
          <div
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            className={`p-3 cursor-pointer transition-colors ${
              activeChatId === chat.id
                ? 'bg-gray-800 border-l-4 border-blue-500'
                : 'hover:bg-gray-800 border-l-4 border-transparent'
            }`}
          >
            {chat.name}
          </div>
        ))}
      </div>
    </>
  );
}