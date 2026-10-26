import { LogOut, Plus, Shield, Trash2, Edit2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../ui/Button';
import { chatsApi } from '../../api/chats';

interface SidebarProps {
  chats: any[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onCreateChat: () => void;
  onLogout: () => void;
  isAdmin?: boolean;
  onChatDeleted: () => void;
}

export function Sidebar({
  chats,
  activeChatId,
  onSelectChat,
  onCreateChat,
  onLogout,
  isAdmin,
  onChatDeleted,
}: SidebarProps) {
  const handleRename = async (e: React.MouseEvent, id: string, currentName: string) => {
    e.stopPropagation();
    const newName = prompt('Новое название:', currentName);
    if (newName && newName !== currentName) {
      try {
        await chatsApi.renameChat(id, newName);
        onChatDeleted(); // Обновляем список
      } catch (err: any) {
        alert(err.message);
      }
    }
  };

  const handleDelete = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    if (!confirm('Переместить чат в корзину?')) return;

    try {
      await chatsApi.softDeleteChat(chatId);
      onChatDeleted();
    } catch (err: any) {
      alert(err.message);
    }
  };

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
            className={`group flex items-center justify-between p-3 cursor-pointer transition-colors ${
              activeChatId === chat.id
                ? 'bg-gray-800 border-l-4 border-blue-500'
                : 'hover:bg-gray-800 border-l-4 border-transparent'
            }`}
          >
            <span className="truncate pr-2 flex-1">{chat.name}</span>
            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={(e) => handleRename(e, chat.id, chat.name)}
                className="text-gray-500 hover:text-blue-500"
                title="Переименовать"
              >
                <Edit2 size={16} />
              </button>
              <button
                onClick={(e) => handleDelete(e, chat.id)}
                className="text-gray-500 hover:text-red-500"
                title="Удалить в корзину"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}