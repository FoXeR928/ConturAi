import { LogOut, Plus } from 'lucide-react';
import { Button } from '../../ui/Button';

interface SidebarProps {
  chats: any[];
  activeChatId: number | null;
  onSelectChat: (id: number) => void;
  onCreateChat: () => void;
  onLogout: () => void;
}

export function Sidebar({ chats, activeChatId, onSelectChat, onCreateChat, onLogout }: SidebarProps) {
  return (
    <>
      <div className="p-4 border-b border-gray-800 flex justify-between items-center">
        <h1 className="font-bold text-lg">ConturAI</h1>
        <button onClick={onLogout} className="text-gray-400 hover:text-white transition-colors">
          <LogOut size={20} />
        </button>
      </div>
      <div className="p-4">
        <Button onClick={onCreateChat} className="w-full flex justify-center gap-2">
          <Plus size={18} /> Новый чат
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {chats.map(chat => (
          <div
            key={chat.id}
            onClick={() => onSelectChat(chat.id)}
            className={`p-3 cursor-pointer transition-colors ${
              activeChatId === chat.id ? 'bg-gray-800 border-l-4 border-blue-500' : 'hover:bg-gray-800 border-l-4 border-transparent'
            }`}
          >
            {chat.name}
          </div>
        ))}
      </div>
    </>
  );
}