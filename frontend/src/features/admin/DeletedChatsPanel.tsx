import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { RotateCcw, Trash2 } from 'lucide-react';
import { chatsApi } from '../../api/chats';

export function DeletedChatsPanel() {
  const [chats, setChats] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await chatsApi.getDeletedChats();
      setChats(data.chats || []);
      setSelected([]);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const toggleSelect = (id: string) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const recover = async () => {
    if (selected.length === 0) return;
    try {
      await chatsApi.recoverChats(selected);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const purge = async () => {
    if (selected.length === 0) return;
    if (!confirm(`Удалить НАВСЕГДА ${selected.length} чатов?`)) return;
    try {
      await chatsApi.purgeDeletedChats(selected);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const purgeAll = async () => {
    if (!confirm('Очистить корзину полностью? Это действие нельзя отменить.')) return;
    try {
      await chatsApi.purgeAllDeletedChats();
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Корзина чатов</h2>
        <div className="flex gap-2">
          <Button onClick={recover} disabled={selected.length === 0} variant="secondary">
            <RotateCcw size={16} className="mr-1" /> Восстановить
          </Button>
          <Button onClick={purge} disabled={selected.length === 0} variant="danger">
            <Trash2 size={16} className="mr-1" /> Удалить выбранные
          </Button>
          <Button onClick={purgeAll} variant="danger">
             Очистить всё
          </Button>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3 w-10">
                <input
                  type="checkbox"
                  onChange={(e) => setSelected(e.target.checked ? chats.map(c => c.id) : [])}
                  checked={selected.length === chats.length && chats.length > 0}
                />
              </th>
              <th className="p-3">Название</th>
              <th className="p-3">Владелец</th>
            </tr>
          </thead>
          <tbody>
            {chats.map((chat) => (
              <tr key={chat.id} className="border-t">
                <td className="p-3">
                  <input
                    type="checkbox"
                    checked={selected.includes(chat.id)}
                    onChange={() => toggleSelect(chat.id)}
                  />
                </td>
                <td className="p-3">{chat.name}</td>
                <td className="p-3 text-gray-500">{chat.user_login}</td>
              </tr>
            ))}
            {chats.length === 0 && (
              <tr>
                <td colSpan={3} className="p-6 text-center text-gray-500">
                  Корзина пуста
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}