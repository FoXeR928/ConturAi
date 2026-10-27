import { Plus, Shield, Trash2, Edit2, LogOut } from 'lucide-react';
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
    if (newName && newName.trim() && newName !== currentName) {
      try {
        await chatsApi.renameChat(id, newName.trim());
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
    <div className="flex flex-col h-full bg-gray-900 text-white">
      {/* Шапка с логотипом и кнопкой выхода */}
      <div className="p-4 border-b border-gray-800 flex justify-between items-center shrink-0">
        <h1 className="font-bold text-lg">ConturAI</h1>
        <button onClick={onLogout} className="text-gray-400 hover:text-white transition-colors" title="Выйти">
          <LogOut size={20} />
        </button>
      </div>

      {/* Кнопки управления */}
      <div className="p-4 space-y-2 shrink-0">
        <Button onClick={onCreateChat} className="w-full flex justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white">
          <Plus size={18} /> Новый чат
        </Button>
        {isAdmin && (
          <Link
            to="/admin"
            className="flex items-center gap-2 justify-center w-full px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm transition-colors"
          >
            <Shield size={16} /> Администрирование
          </Link>
        )}
      </div>

      {/* Список чатов */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
        {chats.map((chat) => {
          const isActive = activeChatId === chat.id;
          return (
            <div
              key={chat.id}
              onClick={() => onSelectChat(chat.id)}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                isActive
                  ? 'bg-gray-800 border-l-4 border-blue-500 shadow-sm'
                  : 'border-l-4 border-transparent hover:bg-gray-800/50 hover:border-gray-600'
              }`}
            >
              <span className={`truncate pr-2 flex-1 text-sm ${isActive ? 'font-medium text-white' : 'text-gray-300'}`}>
                {chat.name}
              </span>
              
              {/* Кнопки действий (появляются при наведении) */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => handleRename(e, chat.id, chat.name)}
                  className="p-1 text-gray-500 hover:text-blue-400 hover:bg-gray-700 rounded transition-colors"
                  title="Переименовать"
                >
                  <Edit2 size={14} />
                </button>
                <button
                  onClick={(e) => handleDelete(e, chat.id)}
                  className="p-1 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded transition-colors"
                  title="Удалить в корзину"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}