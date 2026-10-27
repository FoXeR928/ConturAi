import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { RotateCcw, Trash2, AlertTriangle } from 'lucide-react';
import { chatsApi, Chat } from '../../api/chats';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function DeletedChatsPanel() {
  // Используем типизированный массив вместо any[]
  const [chats, setChats] = useState<Chat[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ==========================================================================
  // БЛОК 2: ЗАГРУЗКА ДАННЫХ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await chatsApi.getDeletedChats();
      setChats(data.chats || []);
      setSelected([]); // Сбрасываем выделение при обновлении
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ==========================================================================
  // БЛОК 3: ВЫДЕЛЕНИЕ (SELECTION)
  // ==========================================================================

  const toggleSelect = (id: string) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selected.length === chats.length && chats.length > 0) {
      setSelected([]); // Снять выделение со всех
    } else {
      setSelected(chats.map(c => c.id)); // Выбрать все
    }
  };

  // ==========================================================================
  // БЛОК 4: ДЕЙСТВИЯ (ВОССТАНОВЛЕНИЕ И УДАЛЕНИЕ)
  // ==========================================================================

  const recover = async () => {
    if (selected.length === 0) return;
    setLoading(true);
    try {
      await chatsApi.recoverChats(selected);
      await load(); // Перезагружаем список после восстановления
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const purge = async () => {
    if (selected.length === 0) return;
    if (!confirm(`Удалить НАВСЕГДА ${selected.length} чатов? Это действие нельзя отменить.`)) return;
    
    setLoading(true);
    try {
      await chatsApi.purgeDeletedChats(selected);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const purgeAll = async () => {
    if (chats.length === 0) return;
    if (!confirm('ВНИМАНИЕ! Очистить корзину полностью? Все выбранные чаты будут стерты из базы навсегда.')) return;
    
    setLoading(true);
    try {
      await chatsApi.purgeAllDeletedChats();
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      {/* Шапка с кнопками */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Trash2 size={24} className="text-gray-400" /> Корзина чатов
          </h2>
          <p className="text-sm text-gray-500 mt-1">Удаленные чаты хранятся здесь до полной очистки.</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <Button 
            onClick={recover} 
            disabled={selected.length === 0 || loading} 
            variant="secondary"
            className="flex items-center"
          >
            <RotateCcw size={16} className="mr-1.5" /> Восстановить
          </Button>
          
          <Button 
            onClick={purge} 
            disabled={selected.length === 0 || loading} 
            variant="danger"
            className="flex items-center"
          >
            <Trash2 size={16} className="mr-1.5" /> Удалить выбранные
          </Button>

          <Button 
            onClick={purgeAll} 
            disabled={chats.length === 0 || loading} 
            variant="danger"
            className="flex items-center bg-red-800 hover:bg-red-900"
          >
            <AlertTriangle size={16} className="mr-1.5" /> Очистить всё
          </Button>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      {/* Таблица */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[500px]">
            <thead className="bg-gray-100 text-left border-b">
              <tr>
                <th className="p-3 w-12 text-center">
                  <input
                    type="checkbox"
                    className="w-4 h-4 cursor-pointer"
                    onChange={toggleSelectAll}
                    checked={selected.length === chats.length && chats.length > 0}
                  />
                </th>
                <th className="p-3">Название чата</th>
                <th className="p-3">Владелец</th>
              </tr>
            </thead>
            <tbody>
              {chats.map((chat) => {
                const isSelected = selected.includes(chat.id);
                return (
                  <tr 
                    key={chat.id} 
                    onClick={() => toggleSelect(chat.id)}
                    className={`border-t cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50 hover:bg-blue-100' : 'hover:bg-gray-50'
                    }`}
                  >
                    <td className="p-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        className="w-4 h-4 cursor-pointer"
                        checked={isSelected}
                        onChange={() => toggleSelect(chat.id)}
                      />
                    </td>
                    <td className="p-3 font-medium text-gray-800">{chat.name}</td>
                    <td className="p-3 text-gray-500 font-mono text-xs">{chat.user_login}</td>
                  </tr>
                );
              })}
              
              {chats.length === 0 && (
                <tr>
                  <td colSpan={3} className="p-8 text-center text-gray-400">
                    <Trash2 size={32} className="mx-auto mb-2 opacity-20" />
                    Корзина пуста
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}