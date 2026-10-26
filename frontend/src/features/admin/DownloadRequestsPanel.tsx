import { useEffect, useState } from 'react';
import { downloadsApi } from '../../api/downloads';
import { Button } from '../../ui/Button';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export function DownloadRequestsPanel() {
  const [requests, setRequests] = useState<any[]>([]);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await downloadsApi.listRequests();
      setRequests(data.requests || []);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      await downloadsApi.processRequest(id, action);
      load();
    } catch (e: any) {
      alert(e.message);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Запросы на скачивание</h2>
        <Button onClick={load} variant="secondary">Обновить</Button>
      </div>
      
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3">Пользователь</th>
              <th className="p-3">Документ</th>
              <th className="p-3">Дата запроса</th>
              <th className="p-3">Статус</th>
              <th className="p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="p-3 font-mono text-xs">{r.user_login}</td>
                <td className="p-3">{r.original_name}</td>
                <td className="p-3 text-gray-500">{new Date(r.created_at).toLocaleString()}</td>
                <td className="p-3">
                  {r.status === 'pending' && <span className="text-yellow-600 flex items-center gap-1"><Clock size={14}/> Ожидает</span>}
                  {r.status === 'approved' && <span className="text-green-600 flex items-center gap-1"><CheckCircle size={14}/> Одобрено</span>}
                  {r.status === 'rejected' && <span className="text-red-600 flex items-center gap-1"><XCircle size={14}/> Отклонено</span>}
                </td>
                <td className="p-3 space-x-2">
                  {r.status === 'pending' && (
                    <>
                      <button onClick={() => handleAction(r.id, 'approve')} className="text-green-600 hover:underline">Разрешить</button>
                      <button onClick={() => handleAction(r.id, 'reject')} className="text-red-600 hover:underline">Отклонить</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {requests.length === 0 && (
              <tr>
                <td colSpan={5} className="p-6 text-center text-gray-500">Нет запросов</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}