import { useEffect, useState } from 'react';
import { systemApi } from '../../api/system';
import { Button } from '../../ui/Button';
import { Database, Download, Trash2, HardDriveDownload } from 'lucide-react';
import { getToken } from '../../api/http';

function formatBytes(bytes: number) {
  if (!bytes) return '0 Б';
  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function DatabasePanel() {
  const [backups, setBackups] = useState<any[]>([]);
  const [dbSize, setDbSize] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await systemApi.getBackups();
      setBackups(data.backups || []);
      setDbSize(data.db_size || 0);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => { load(); }, []);

  const createBackup = async () => {
    setLoading(true);
    setError('');
    try {
      await systemApi.createBackup();
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const download = async (filename: string) => {
    try {
      const token = getToken();
      const res = await fetch(`/api/system/db/backups/${filename}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Ошибка скачивания');
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const remove = async (filename: string) => {
    if (!confirm(`Удалить бэкап ${filename}?`)) return;
    try {
      await systemApi.deleteBackup(filename);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Database size={24} /> Базы данных
        </h2>
        <Button onClick={createBackup} disabled={loading} className="flex items-center gap-2">
          <HardDriveDownload size={18} /> {loading ? 'Создание...' : 'Создать бэкап'}
        </Button>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-white p-4 rounded-lg shadow mb-6 flex justify-between items-center">
        <div>
          <div className="text-sm text-gray-500">Текущий размер базы данных (PostgreSQL)</div>
          <div className="text-2xl font-bold">{formatBytes(dbSize)}</div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3">Имя файла</th>
              <th className="p-3">Размер</th>
              <th className="p-3">Дата создания</th>
              <th className="p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {backups.map((b) => (
              <tr key={b.name} className="border-t">
                <td className="p-3 font-mono text-xs">{b.name}</td>
                <td className="p-3">{formatBytes(b.size)}</td>
                <td className="p-3 text-gray-500">{new Date(b.created_at).toLocaleString()}</td>
                <td className="p-3 space-x-3">
                  <button onClick={() => download(b.name)} className="text-blue-600 hover:underline inline-flex items-center gap-1">
                    <Download size={14} /> Скачать
                  </button>
                  <button onClick={() => remove(b.name)} className="text-red-600 hover:underline inline-flex items-center gap-1">
                    <Trash2 size={14} /> Удалить
                  </button>
                </td>
              </tr>
            ))}
            {backups.length === 0 && (
              <tr><td colSpan={4} className="p-6 text-center text-gray-500">Бэкапов пока нет</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}