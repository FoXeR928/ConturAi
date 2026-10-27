import { useEffect, useState } from 'react';
import { downloadsApi, DownloadRequestItem } from '../../api/downloads';
import { Button } from '../../ui/Button';
import { CheckCircle, XCircle, Clock, RefreshCw, Download, FileText, MessageSquare } from 'lucide-react';
import { useToast } from '../../components/ToastContext';

export function DownloadRequestsPanel() {
  const [requests, setRequests] = useState<DownloadRequestItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { toast } = useToast();

  const load = async () => {
    setLoading(true);
    try {
      const data = await downloadsApi.listRequests();
      setRequests(data.requests || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    setLoading(true);
    try {
      await downloadsApi.processRequest(id, action);
      toast(
        action === 'approve' ? 'Доступ разрешен на 24 часа' : 'В скачивании отказано',
        action === 'approve' ? 'success' : 'info'
      );
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Download size={24} className="text-blue-600" /> Запросы на скачивание
          </h2>
          <p className="text-sm text-gray-500 mt-1">Пользователи, ожидающие разрешения на скачивание.</p>
        </div>
        <Button onClick={load} disabled={loading} variant="secondary" className="flex items-center gap-2 self-start sm:self-auto">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Обновить
        </Button>
      </div>
      
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[650px]">
            <thead className="bg-gray-100 text-left border-b">
              <tr>
                <th className="p-3">Пользователь</th>
                <th className="p-3">Объект</th>
                <th className="p-3">Дата запроса</th>
                <th className="p-3">Статус</th>
                <th className="p-3">Действия</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id} className="border-t hover:bg-gray-50 transition-colors">
                  <td className="p-3 font-mono text-xs font-semibold">{r.user_login}</td>
                  
                  {/* Объект (документ или чат) */}
                  <td className="p-3 font-medium">
                    {r.file_name ? (
                      <span className="flex items-center gap-1.5 text-blue-600">
                        <FileText size={14} /> {r.file_name}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-purple-600">
                        <MessageSquare size={14} /> Чат: {r.chat_name}
                      </span>
                    )}
                  </td>
                  
                  <td className="p-3 text-gray-500 whitespace-nowrap">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  
                  <td className="p-3">
                    {r.status === 'pending' && (
                      <span className="inline-flex items-center gap-1 text-yellow-600 font-medium text-xs bg-yellow-50 px-2 py-1 rounded">
                        <Clock size={14}/> Ожидает
                      </span>
                    )}
                    {r.status === 'approved' && (
                      <span className="inline-flex items-center gap-1 text-green-600 font-medium text-xs bg-green-50 px-2 py-1 rounded">
                        <CheckCircle size={14}/> Одобрено
                      </span>
                    )}
                    {r.status === 'rejected' && (
                      <span className="inline-flex items-center gap-1 text-red-600 font-medium text-xs bg-red-50 px-2 py-1 rounded">
                        <XCircle size={14}/> Отклонено
                      </span>
                    )}
                  </td>
                  
                  <td className="p-3 space-x-3">
                    {r.status === 'pending' ? (
                      <>
                        <button 
                          onClick={() => handleAction(r.id, 'approve')} 
                          disabled={loading}
                          className="text-green-600 hover:text-green-800 font-medium hover:underline disabled:opacity-50 inline-flex items-center gap-1"
                        >
                          <CheckCircle size={14} /> Разрешить
                        </button>
                        <button 
                          onClick={() => handleAction(r.id, 'reject')} 
                          disabled={loading}
                          className="text-red-600 hover:text-red-800 font-medium hover:underline disabled:opacity-50 inline-flex items-center gap-1"
                        >
                          <XCircle size={14} /> Отклонить
                        </button>
                      </>
                    ) : (
                      <span className="text-gray-400 text-xs italic">Обработано</span>
                    )}
                  </td>
                </tr>
              ))}
              
              {requests.length === 0 && !loading && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-gray-500">
                    <CheckCircle size={32} className="mx-auto mb-2 text-green-300" />
                    Нет активных запросов на скачивание
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