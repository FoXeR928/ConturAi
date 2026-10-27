import { useState } from 'react';
import { Plus, Shield, Trash2, Edit2, LogOut, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../ui/Button';
import { chatsApi, Chat } from '../../api/chats';
import { useToast } from '../../components/ToastContext';

// ==============================================================================
// БЛОК 1: ТИПИЗАЦИЯ
// ==============================================================================

interface SidebarProps {
  chats: Chat[]; // <-- Используем типизированный массив
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onCreateChat: () => void;
  onLogout: () => void;
  isAdmin?: boolean;
  onChatDeleted: () => void; // Вызывается для обновления списка после изменений
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function Sidebar({
  chats,
  activeChatId,
  onSelectChat,
  onCreateChat,
  onLogout,
  isAdmin,
  onChatDeleted,
}: SidebarProps) {
  // Храним ID чата, с которым сейчас происходит действие (удаление или переименование)
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const { toast } = useToast();

  // ==========================================================================
  // БЛОК 3: ДЕЙСТВИЯ (ПЕРЕИМЕНОВАНИЕ И УДАЛЕНИЕ)
  // ==========================================================================

  const handleRename = async (e: React.MouseEvent, id: string, currentName: string) => {
    e.stopPropagation(); // Чтобы клик не открывал чат
    
    const newName = prompt('Новое название:', currentName);
    if (!newName || !newName.trim() || newName === currentName) return;

    setActionLoading(id);
    try {
      await chatsApi.renameChat(id, newName.trim());
      onChatDeleted(); // Обновляем список в родительском компоненте
      toast('Чат переименован', 'success');
    } catch (err: any) {
      toast(err.message, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    if (!confirm('Переместить чат в корзину?')) return;

    setActionLoading(chatId);
    try {
      await chatsApi.softDeleteChat(chatId);
      onChatDeleted();
      toast('Чат перемещен в корзину', 'info');
    } catch (err: any) {
      toast(err.message, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  // ==========================================================================
  // БЛОК 4: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div className="flex flex-col h-full bg-gray-900 text-white select-none">
      
      {/* Шапка с логотипом и кнопкой выхода */}
      <div className="p-4 border-b border-gray-800 flex justify-between items-center shrink-0">
        <h1 className="font-bold text-lg tracking-wide text-gray-100">ConturAI</h1>
        <button 
          onClick={onLogout} 
          className="text-gray-400 hover:text-white transition-colors p-1.5 rounded-md hover:bg-gray-800" 
          title="Выйти"
        >
          <LogOut size={20} />
        </button>
      </div>

      {/* Кнопки управления */}
      <div className="p-4 space-y-2 shrink-0">
        <Button 
          onClick={onCreateChat} 
          className="w-full flex justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all"
        >
          <Plus size={18} /> Новый чат
        </Button>
        
        {isAdmin && (
          <Link
            to="/admin"
            className="flex items-center gap-2 justify-center w-full px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm transition-colors border border-gray-700"
          >
            <Shield size={16} className="text-purple-400" /> Администрирование
          </Link>
        )}
      </div>

      {/* Список чатов */}
      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1 scrollbar-thin scrollbar-thumb-gray-700">
        {chats.map((chat) => {
          const isActive = activeChatId === chat.id;
          const isBusy = actionLoading === chat.id;

          return (
            <div
              key={chat.id}
              onClick={() => !isBusy && onSelectChat(chat.id)}
              className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition-all ${
                isActive
                  ? 'bg-gray-800 border-l-4 border-blue-500 shadow-sm'
                  : 'border-l-4 border-transparent hover:bg-gray-800/60 hover:border-gray-600'
              } ${isBusy ? 'opacity-70 pointer-events-none' : ''}`}
            >
              <span className={`truncate pr-2 flex-1 text-sm ${isActive ? 'font-medium text-white' : 'text-gray-300'}`}>
                {chat.name}
              </span>
              
              {/* Кнопки действий (появляются при наведении) */}
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {isBusy ? (
                  // Спиннер, если идет удаление/переименование
                  <div className="p-1 text-blue-400">
                    <RefreshCw size={14} className="animate-spin" />
                  </div>
                ) : (
                  // Обычные кнопки
                  <>
                    <button
                      onClick={(e) => handleRename(e, chat.id, chat.name)}
                      className="p-1.5 text-gray-500 hover:text-blue-400 hover:bg-gray-700 rounded transition-colors"
                      title="Переименовать"
                    >
                      <Edit2 size={14} />
                    </button>
                    <button
                      onClick={(e) => handleDelete(e, chat.id)}
                      className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-gray-700 rounded transition-colors"
                      title="Удалить в корзину"
                    >
                      <Trash2 size={14} />
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
        
        {/* Заглушка, если чатов нет */}
        {chats.length === 0 && (
          <div className="text-center text-gray-500 text-sm mt-10">
            Нет чатов.<br/>Создайте новый!
          </div>
        )}
      </div>
    </div>
  );
}