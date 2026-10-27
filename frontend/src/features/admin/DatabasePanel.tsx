import { useEffect, useState } from 'react';
import { systemApi, BackupFile } from '../../api/system';
import { Button } from '../../ui/Button';
import { Database, Download, Trash2, HardDriveDownload } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ==============================================================================

/** Преобразует байты в удобочитаемый формат (КБ, МБ, ГБ). */
function formatBytes(bytes: number) {
  if (!bytes) return '0 Б';
  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function DatabasePanel() {
  // Используем типизированный массив вместо any[]
  const [backups, setBackups] = useState<BackupFile[]>([]);
  const [dbSize, setDbSize] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // ==========================================================================
  // БЛОК 3: ЗАГРУЗКА СПИСКА БЭКАПОВ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await systemApi.getBackups();
      setBackups(data.backups || []);
      setDbSize(data.db_size || 0);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => { 
    load(); 
  }, []);

  // ==========================================================================
  // БЛОК 4: ДЕЙСТВИЯ (СОЗДАНИЕ, СКАЧИВАНИЕ, УДАЛЕНИЕ)
  // ==========================================================================

  const createBackup = async () => {
    setLoading(true);
    setError('');
    try {
      await systemApi.createBackup();
      load(); // Обновляем список после создания
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const download = async (filename: string) => {
    try {
      // ИСПОЛЬЗУЕМ НАШ ЦЕНТРАЛИЗОВАННЫЙ API-МЕТОД (вместо ручного fetch)
      await systemApi.downloadBackup(filename);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const remove = async (filename: string) => {
    if (!confirm(`Удалить бэкап ${filename}? Это действие нельзя отменить.`)) return;
    try {
      await systemApi.deleteBackup(filename);
      load(); // Обновляем таблицу
    } catch (e: any) {
      setError(e.message);
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      {/* Шапка панели */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Database size={24} className="text-blue-600" /> Базы данных
        </h2>
        <Button onClick={createBackup} disabled={loading} className="flex items-center gap-2">
          <HardDriveDownload size={18} /> {loading ? 'Создание...' : 'Создать бэкап'}
        </Button>
      </div>

      {/* Блок с ошибкой */}
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      {/* Информация о размере БД */}
      <div className="bg-white p-4 rounded-lg shadow mb-6 flex justify-between items-center border-l-4 border-blue-500">
        <div>
          <div className="text-sm text-gray-500 font-medium">Текущий размер базы данных (PostgreSQL)</div>
          <div className="text-2xl font-bold">{formatBytes(dbSize)}</div>
        </div>
        <div className="text-sm text-gray-400 hidden sm:block">
          Включает таблицы, индексы и векторные данные pgvector
        </div>
      </div>

      {/* Таблица бэкапов */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[600px]">
            <thead className="bg-gray-100 text-left border-b">
              <tr>
                <th className="p-3">Имя файла</th>
                <th className="p-3">Размер</th>
                <th className="p-3">Дата создания</th>
                <th className="p-3">Действия</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((b) => (
                <tr key={b.name} className="border-t hover:bg-gray-50 transition-colors">
                  <td className="p-3 font-mono text-xs font-semibold">{b.name}</td>
                  <td className="p-3 text-gray-700">{formatBytes(b.size)}</td>
                  <td className="p-3 text-gray-500">{new Date(b.created_at).toLocaleString()}</td>
                  <td className="p-3 space-x-3">
                    <button 
                      onClick={() => download(b.name)} 
                      className="text-blue-600 hover:text-blue-800 inline-flex items-center gap-1 font-medium transition-colors"
                    >
                      <Download size={14} /> Скачать
                    </button>
                    <button 
                      onClick={() => remove(b.name)} 
                      className="text-red-600 hover:text-red-800 inline-flex items-center gap-1 font-medium transition-colors"
                    >
                      <Trash2 size={14} /> Удалить
                    </button>
                  </td>
                </tr>
              ))}
              
              {backups.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-8 text-center text-gray-500">
                    Бэкапов пока нет. Нажмите «Создать бэкап», чтобы сделать первый.
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