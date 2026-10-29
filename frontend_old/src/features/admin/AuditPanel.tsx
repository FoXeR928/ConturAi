import { useEffect, useState } from 'react';
import { auditApi, AuditLogItem } from '../../api/audit';
import { Button } from '../../ui/Button';
import { RefreshCw, ClipboardList } from 'lucide-react';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function AuditPanel() {
  // Используем типизированный массив вместо any[]
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Пагинация
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const LIMIT = 50;

  // ==========================================================================
  // БЛОК 2: ЗАГРУЗКА ДАННЫХ
  // ==========================================================================

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await auditApi.getLogs(LIMIT, offset);
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Перезагружаем при смене страницы
  useEffect(() => { 
    load(); 
  }, [offset]);

  // ==========================================================================
  // БЛОК 3: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (ВИЗУАЛИЗАЦИЯ)
  // ==========================================================================

  /** Красит бейджик действия в зависимости от типа (удаление — красный, загрузка — зеленый и т.д.) */
  const getActionBadge = (action: string) => {
    if (action.includes('delete')) return 'bg-red-100 text-red-700 border-red-200';
    if (action.includes('upload')) return 'bg-green-100 text-green-700 border-green-200';
    if (action.includes('login')) return 'bg-blue-100 text-blue-700 border-blue-200';
    return 'bg-gray-100 text-gray-700 border-gray-200';
  };

  // ==========================================================================
  // БЛОК 4: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      {/* Шапка */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <ClipboardList size={24} className="text-blue-600" /> Журнал событий
        </h2>
        <Button onClick={load} disabled={loading} variant="secondary" className="flex items-center gap-2">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Загрузка...' : 'Обновить'}
        </Button>
      </div>
      
      {/* Ошибки */}
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      {/* Таблица (с горизонтальным скроллом для мобильных) */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[700px]">
            <thead className="bg-gray-100 text-left border-b">
              <tr>
                <th className="p-3">Дата</th>
                <th className="p-3">Пользователь</th>
                <th className="p-3">Действие</th>
                <th className="p-3">Детали</th>
                <th className="p-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-t hover:bg-gray-50 transition-colors">
                  {/* Дата */}
                  <td className="p-3 text-gray-500 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  
                  {/* Пользователь */}
                  <td className="p-3 font-mono text-xs font-semibold">{log.user_login}</td>
                  
                  {/* Действие */}
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium border ${getActionBadge(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  
                  {/* Детали (с обрезкой длинного текста) */}
                  <td className="p-3 text-gray-600 max-w-xs truncate" title={log.details}>
                    {log.details || '—'}
                  </td>
                  
                  {/* IP-адрес */}
                  <td className="p-3 text-gray-400 font-mono text-xs">{log.ip_address || '—'}</td>
                </tr>
              ))}
              
              {/* Пустое состояние */}
              {logs.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    Событий пока нет
                  </td>
                </tr>
              )}
              
              {/* Скелетон загрузки (опционально) */}
              {loading && logs.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-400 animate-pulse">
                    Загрузка событий...
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Пагинация */}
      <div className="flex justify-between items-center mt-4">
        <span className="text-sm text-gray-500">
          Всего записей: <b>{total}</b> (показано {offset + 1}–{Math.min(offset + LIMIT, total)})
        </span>
        <div className="flex gap-2">
          <Button 
            onClick={() => setOffset(Math.max(0, offset - LIMIT))} 
            disabled={offset === 0 || loading} 
            variant="secondary"
          >
            Назад
          </Button>
          <Button 
            onClick={() => setOffset(offset + LIMIT)} 
            disabled={offset + LIMIT >= total || loading} 
            variant="secondary"
          >
            Вперед
          </Button>
        </div>
      </div>
    </div>
  );
}