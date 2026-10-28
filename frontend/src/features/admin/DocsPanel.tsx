import { useEffect, useRef, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { TagSelect } from '../../ui/TagSelect';
import { Upload, FileText, Download, Trash2, Clock } from 'lucide-react';
import { docsApi } from '../../api/docs';
import { downloadsApi } from '../../api/downloads';
import { useToast } from '../../components/ToastContext';

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

export function DocsPanel() {
  const [name, setName] = useState('');
  const [text, setText] = useState('');
  const [fileText, setFileText] = useState('');
  const [file, setFile] = useState<string>('');
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [uploads, setUploads] = useState<UploadRow[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // Разделяем теги
  const [textTags, setTextTags] = useState<string[]>([]);
  const [fileTags, setFileTags] = useState<string[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [downloadStatuses, setDownloadStatuses] = useState<Record<string, 'idle' | 'pending'>>({});

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

  const readFile = async (f: File) => {
    if (f.size > 20 * 1024 * 1024) {
      toast('Файл слишком большой (макс 20 МБ)', 'error');
      return;
    }
    setFile(f.name);
    setLoading(true);
    try {
      const data = await docsApi.readDoc(f);
      if (data.result) {
        setFileText(data.file_text);
        setUploadId(data.upload_id);
        if (!name) setName(data.file_name);
      } else {
        toast(data.message, 'error');
      }
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const add = async (isFile: boolean) => {
    const finalText = isFile ? fileText : text;
    const finalName = isFile ? (name || file) : name;
    const finalUploadId = isFile ? uploadId : null;
    const finalTags = isFile ? fileTags : textTags;

    if (!finalText.trim() || !finalName.trim()) {
      toast('Заполните имя и текст', 'error');
      return;
    }

    try {
      const data = await docsApi.addDoc(finalName, finalText, finalUploadId ?? undefined, finalTags);
      toast(data.message, 'success');
      
      if (isFile) {
        setFileTags([]);
        setFileText('');
        setFile('');
        setUploadId(null);
      } else {
        setTextTags([]);
        setText('');
      }
      setName('');
      loadList();
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  const download = async (u: UploadRow) => {
    const currentStatus = downloadStatuses[u.id] || 'idle';
    if (currentStatus === 'pending') {
      toast('Ваш запрос ожидает одобрения администратора', 'info');
      return;
    }

    try {
      await docsApi.downloadDoc(u.id, u.original_name);
    } catch (e: any) {
      if (e.status === 403 || e.message?.includes('запрещено')) {
        try {
          await downloadsApi.requestAccess({ uploadId: u.id });
          setDownloadStatuses(prev => ({ ...prev, [u.id]: 'pending' }));
          toast('Запрос на скачивание отправлен администратора', 'success');
        } catch (reqErr: any) {
          if (reqErr.message?.includes('уже создана')) {
            setDownloadStatuses(prev => ({ ...prev, [u.id]: 'pending' }));
            toast('Запрос уже в обработке', 'info');
          } else {
            toast(reqErr.message, 'error');
          }
        }
      } else {
        toast(e.message, 'error');
      }
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

  return (
    <div>
      {/* Красивый заголовок */}
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-gray-800">
        <FileText size={24} className="text-blue-600" /> Документы и База Знаний
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Форма текста */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <FileText size={18} className="text-gray-400" /> Текст вручную
          </h3>
          <Input 
            placeholder="Имя документа" 
            value={name} 
            onChange={(e) => setName(e.target.value)} 
          />
          <div className="mt-3">
            <TagSelect selected={textTags} onChange={setTextTags} placeholder="Выбрать теги..." />
          </div>
          <textarea
            className="w-full border border-gray-300 rounded-lg p-3 mt-3 font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            rows={5}
            placeholder="Вставьте текст..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <Button 
            onClick={() => add(false)} 
            disabled={!text.trim() || !name.trim()} 
            className="w-full mt-3"
          >
            Загрузить в RAG
          </Button>
        </div>

        {/* Форма файла */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <Upload size={18} className="text-gray-400" /> Файл (PDF/DOCX/XLSX)
          </h3>
          <input
            type="file"
            ref={fileInput}
            className="hidden"
            accept=".pdf,.docx,.xlsx"
            onChange={(e) => e.target.files?.[0] && readFile(e.target.files[0])}
          />
          <Button 
            onClick={() => fileInput.current?.click()} 
            className="w-full bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300" 
            disabled={loading}
          >
            {loading ? 'Обработка файла...' : 'Выбрать файл'}
          </Button>
          
          {file && <div className="text-sm font-medium text-gray-700 mt-3">Выбран: {file}</div>}
          
          <div className="mt-3">
            <TagSelect selected={fileTags} onChange={setFileTags} placeholder="Выбрать теги для файла..." />
          </div>
          
          {fileText && (
            <textarea
              className="w-full border border-gray-300 rounded-lg p-3 mt-3 font-mono text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              rows={4}
              value={fileText}
              onChange={(e) => setFileText(e.target.value)}
            />
          )}
          <Button
            onClick={() => add(true)}
            disabled={!fileText.trim() || loading}
            className="w-full mt-3"
            variant="secondary"
          >
            Загрузить в RAG
          </Button>
        </div>
      </div>

      {/* Таблица */}
      <div className="mt-8">
        <h3 className="text-xl font-bold mb-3 text-gray-800">Уже загруженные</h3>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[800px]">
              <thead className="bg-gray-50 text-left border-b border-gray-200">
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
                {uploads.map((u) => {
                  const isPending = downloadStatuses[u.id] === 'pending';
                  return (
                    <tr key={u.id} className="border-t border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="p-3 font-medium">{u.original_name}</td>
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
                      <td className="p-3 text-gray-600">{u.size ? `${Math.round(u.size / 1024)} КБ` : '—'}</td>
                      <td className="p-3">{u.chunks_count}</td>
                      <td className="p-3 text-gray-500 font-mono text-xs">{u.uploaded_by || '—'}</td>
                      <td className="p-3 space-x-3">
                        <button
                          onClick={() => download(u)}
                          className={`inline-flex items-center gap-1 font-medium transition-colors ${isPending ? 'text-yellow-600' : 'text-blue-600 hover:text-blue-800'}`}
                          disabled={!u.mime_type || isPending}
                        >
                          {isPending ? <><Clock size={14} /> Ожидание</> : <><Download size={14} /> Скачать</>}
                        </button>
                        <button onClick={() => remove(u)} className="text-red-600 hover:text-red-800 inline-flex items-center gap-1 font-medium">
                          <Trash2 size={14} /> Удалить
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {uploads.length === 0 && (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-gray-500">
                      <FileText size={32} className="mx-auto mb-2 text-gray-300" />
                      Нет загруженных документов
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}