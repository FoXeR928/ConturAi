import { useEffect, useState } from 'react';
import { auditApi } from '../../api/audit';
import { Button } from '../../ui/Button';

export function AuditPanel() {
  const [logs, setLogs] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const LIMIT = 50;

  const load = async () => {
    try {
      const data = await auditApi.getLogs(LIMIT, offset);
      setLogs(data.logs || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => { load(); }, [offset]);

  const getActionBadge = (action: string) => {
    if (action.includes('delete')) return 'bg-red-100 text-red-700';
    if (action.includes('upload')) return 'bg-green-100 text-green-700';
    if (action.includes('login')) return 'bg-blue-100 text-blue-700';
    return 'bg-gray-100 text-gray-700';
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Журнал событий</h2>
        <Button onClick={load} variant="secondary">Обновить</Button>
      </div>
      
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
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
              <tr key={log.id} className="border-t">
                <td className="p-3 text-gray-500 whitespace-nowrap">
                  {new Date(log.created_at).toLocaleString()}
                </td>
                <td className="p-3 font-mono text-xs">{log.user_login}</td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getActionBadge(log.action)}`}>
                    {log.action}
                  </span>
                </td>
                <td className="p-3 text-gray-600 max-w-xs truncate" title={log.details}>{log.details || '—'}</td>
                <td className="p-3 text-gray-400 font-mono text-xs">{log.ip_address || '—'}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr><td colSpan={5} className="p-6 text-center text-gray-500">Событий пока нет</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center mt-4">
        <span className="text-sm text-gray-500">Всего записей: {total}</span>
        <div className="flex gap-2">
          <Button onClick={() => setOffset(Math.max(0, offset - LIMIT))} disabled={offset === 0} variant="secondary">Назад</Button>
          <Button onClick={() => setOffset(offset + LIMIT)} disabled={offset + LIMIT >= total} variant="secondary">Вперед</Button>
        </div>
      </div>
    </div>
  );
}