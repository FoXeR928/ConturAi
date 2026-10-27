import { useEffect, useRef, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Upload, FileText, Download, Trash2 } from 'lucide-react';
import { docsApi } from '../../api/docs';
import { TagInput } from '../../ui/TagInput';
import { useToast } from '../../components/ToastContext';

// ==============================================================================
// БЛОК 1: ТИПИЗАЦИЯ ДАННЫХ
// ==============================================================================

interface UploadRow {
  id: string;
  original_name: string;
  mime_type: string | null;
  size: number;
  chunks_count: number;
  uploaded_by: string | null;
  created_at: string;
  tags?: string[];
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function DocsPanel() {
  // --- Состояния для ручного ввода текста ---
  const [name, setName] = useState('');
  const [text, setText] = useState('');
  
  // --- Состояния для загрузки файла ---
  const [fileText, setFileText] = useState(''); // Извлеченный из файла текст
  const [file, setFile] = useState<string>(''); // Имя выбранного файла
  const [uploadId, setUploadId] = useState<string | null>(null); // ID загрузки на сервере
  
  // --- Общие состояния ---
  const [uploads, setUploads] = useState<UploadRow[]>([]); // Список загруженных документов
  const [tags, setTags] = useState<string[]>([]); // Выбранные теги
  const [loading, setLoading] = useState(false); // Спиннер при парсинге файла
  
  const fileInput = useRef<HTMLInputElement>(null); // Ссылка на скрытый <input type="file">
  const { toast } = useToast();

  // ==========================================================================
  // БЛОК 3: ЗАГРУЗКА СПИСКА ДОКУМЕНТОВ
  // ==========================================================================

  const loadList = async () => {
    try {
      const data = await docsApi.listDocs();
      if (data.result) setUploads(data.uploads || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  // ==========================================================================
  // БЛОК 4: ЧТЕНИЕ ФАЙЛА (ПАРСИНГ НА БЭКЕНДЕ)
  // ==========================================================================

  const readFile = async (f: File) => {
    // 1. Проверка размера (на бэкенде тоже есть проверка, но это экономит трафик)
    if (f.size > 20 * 1024 * 1024) {
      toast('Файл слишком большой (макс 20 МБ)', 'error');
      return;
    }
    
    setFile(f.name);
    setLoading(true);
    
    try {
      // Отправляем файл на бэкенд для извлечения текста и сохранения оригинала
      const data = await docsApi.readDoc(f);
      if (data.result) {
        setFileText(data.file_text); // Показываем распознанный текст в textarea
        setUploadId(data.upload_id); // Запоминаем ID для последующей индексации
        if (!name) setName(data.file_name); // Автоматически подставляем имя файла
      } else {
        toast(data.message, 'error');
      }
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================================
  // БЛОК 5: СОХРАНЕНИЕ В RAG (ИНДЕКСАЦИЯ)
  // ==========================================================================

  const add = async () => {
    try {
      // Логика выбора текста: если пользователь что-то ввел вручную (text), берем это.
      // Иначе берем текст, извлеченный из файла (fileText).
      const finalText = text || fileText;
      
      const data = await docsApi.addDoc(
        name || file || 'document',
        finalText,
        uploadId ?? undefined, // Если есть ID файла, бэкенд свяжет чанки с ним
        tags
      );
      
      toast(data.message, 'success');
      
      // Сброс формы после успешной загрузки
      setTags([]); 
      setName('');
      setText('');
      setFileText('');
      setFile('');
      setUploadId(null);
      
      loadList(); // Обновляем таблицу
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  // ==========================================================================
  // БЛОК 6: СКАЧИВАНИЕ И УДАЛЕНИЕ
  // ==========================================================================

  const download = async (u: UploadRow) => {
    try {
      await docsApi.downloadDoc(u.id, u.original_name);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  const remove = async (u: UploadRow) => {
    if (!confirm(`Удалить «${u.original_name}» и все его чанки?`)) return;
    try {
      await docsApi.deleteDoc(u.id);
      loadList();
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  // ==========================================================================
  // БЛОК 7: РЕНДЕР (ФОРМЫ ДОБАВЛЕНИЯ)
  // ==========================================================================

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Документы</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Форма 1: Ручной ввод текста */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FileText size={18} /> Текст вручную
          </h3>
          <Input placeholder="Имя документа" value={name} onChange={(e) => setName(e.target.value)} />
          <div className="mt-2">
            <TagInput tags={tags} onChange={setTags} placeholder="Теги (Enter для добавления)" />
          </div>
          <textarea
            className="w-full border rounded p-2 mt-3 font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            rows={6}
            placeholder="Вставьте текст..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <Button onClick={add} disabled={!text || !name} className="w-full mt-3">
            Загрузить в RAG
          </Button>
        </div>

        {/* Форма 2: Загрузка файла */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Upload size={18} /> Файл (PDF/DOCX/XLSX)
          </h3>
          <input
            type="file"
            ref={fileInput}
            className="hidden"
            accept=".pdf,.docx,.xlsx"
            onChange={(e) => e.target.files?.[0] && readFile(e.target.files[0])}
          />
          <Button onClick={() => fileInput.current?.click()} className="w-full" disabled={loading}>
            {loading ? 'Обработка файла...' : 'Выбрать файл'}
          </Button>
          
          {file && <div className="text-sm text-gray-600 mt-2">Файл: {file}</div>}
          
          <div className="mt-2">
            <TagInput tags={tags} onChange={setTags} placeholder="Теги для этого файла" />
          </div>
          
          {fileText && (
            <textarea
              className="w-full border rounded p-2 mt-3 font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              rows={5}
              value={fileText}
              onChange={(e) => setFileText(e.target.value)}
            />
          )}
          <Button
            onClick={add}
            disabled={!fileText || loading}
            className="w-full mt-3"
            variant="secondary"
          >
            Загрузить в RAG
          </Button>
        </div>
      </div>

      {/* ======================================================================
          БЛОК 8: ТАБЛИЦА СУЩЕСТВУЮЩИХ ДОКУМЕНТОВ
          ====================================================================== */}
      
      <div className="mt-8">
        <h3 className="text-xl font-bold mb-3">Уже загруженные</h3>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 text-left border-b">
              <tr>
                <th className="p-3">Имя</th>
                <th className="p-3">Теги</th>
                <th className="p-3">Тип</th>
                <th className="p-3">Размер</th>
                <th className="p-3">Чанков</th>
                <th className="p-3">Кто</th>
                <th className="p-3">Действия</th>
              </tr>
            </thead>
            <tbody>
              {uploads.map((u) => (
                <tr key={u.id} className="border-t hover:bg-gray-50 transition-colors">
                  <td className="p-3 font-medium">{u.original_name}</td>
                  
                  {/* Рендер тегов */}
                  <td className="p-3">
                    {u.tags && u.tags.length > 0 ? (
                      <div className="flex gap-1 flex-wrap">
                        {u.tags.map((t, i) => (
                          <span key={i} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">{t}</span>
                        ))}
                      </div>
                    ) : <span className="text-gray-400">—</span>}
                  </td>
                  
                  <td className="p-3 text-xs text-gray-500">{u.mime_type || '—'}</td>
                  
                  {/* Форматирование размера (КБ) */}
                  <td className="p-3 text-gray-600">{u.size ? `${Math.round(u.size / 1024)} КБ` : '—'}</td>
                  
                  <td className="p-3">{u.chunks_count}</td>
                  <td className="p-3 text-gray-500 font-mono text-xs">{u.uploaded_by || '—'}</td>
                  
                  {/* Кнопки действий */}
                  <td className="p-3 space-x-2">
                    <button
                      onClick={() => download(u)}
                      className="text-blue-600 hover:underline inline-flex items-center gap-1 disabled:opacity-50"
                      disabled={!u.mime_type} // Нельзя скачать чисто текстовый документ
                      title={!u.mime_type ? "У текстового документа нет оригинала" : "Скачать оригинал"}
                    >
                      <Download size={14} /> Скачать
                    </button>
                    <button
                      onClick={() => remove(u)}
                      className="text-red-600 hover:underline inline-flex items-center gap-1"
                    >
                      <Trash2 size={14} /> Удалить
                    </button>
                  </td>
                </tr>
              ))}
              {uploads.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-6 text-center text-gray-500">
                    Нет загруженных документов
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