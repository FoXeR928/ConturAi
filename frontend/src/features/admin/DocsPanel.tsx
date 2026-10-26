import { useEffect, useRef, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Upload, FileText, Download, Trash2 } from 'lucide-react';
import { docsApi } from '../../api/docs';
import { TagInput } from '../../ui/TagInput';
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
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploads, setUploads] = useState<UploadRow[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const [tags, setTags] = useState<string[]>([]);

  const loadList = async () => {
    try {
      const data = await docsApi.listDocs();
      if (data.result) setUploads(data.uploads || []);
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    loadList();
  }, []);

  const readFile = async (f: File) => {
    setError('');
    setFile(f.name);
    try {
      const data = await docsApi.readDoc(f);
      if (data.result) {
        setFileText(data.file_text);
        setUploadId(data.upload_id);
        if (!name) setName(data.file_name);
      } else {
        setError(data.message);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const add = async () => {
    setError('');
    setSuccess('');
    try {
      const data = await docsApi.addDoc(
        name || file || 'document',
        text || fileText,
        uploadId ?? undefined,
        tags,
      );
      toast(data.message, 'success');
      setTags([]); 
      setName('');
      setText('');
      setFileText('');
      setFile('');
      setUploadId(null);
      loadList();
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  const download = async (u: UploadRow) => {
    setError('');
    setSuccess('');
    try {
      await docsApi.downloadDoc(u.id, u.original_name);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const remove = async (u: UploadRow) => {
    if (!confirm(`Удалить «${u.original_name}» и все его чанки?`)) return;
    try {
      await docsApi.deleteDoc(u.id);
      loadList();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Документы</h2>
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}
      {success && <div className="bg-green-50 text-green-700 p-3 rounded mb-4">{success}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <FileText size={18} /> Текст вручную
          </h3>
          <Input placeholder="Имя документа" value={name} onChange={(e) => setName(e.target.value)} />
          <textarea
            className="w-full border rounded p-2 mt-3 font-mono text-sm"
            rows={8}
            placeholder="Вставьте текст..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <Button onClick={add} disabled={!text || !name} className="w-full mt-3">
            Загрузить в RAG
          </Button>
        </div>

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
          <Button onClick={() => fileInput.current?.click()} className="w-full">
            Выбрать файл
          </Button>
          {file && <div className="text-sm text-gray-600 mt-2">Файл: {file}</div>}
          {fileText && (
            <textarea
              className="w-full border rounded p-2 mt-3 font-mono text-sm"
              rows={8}
              value={fileText}
              onChange={(e) => setFileText(e.target.value)}
            />
          )}
          <Button
            onClick={add}
            disabled={!fileText}
            className="w-full mt-3"
            variant="secondary"
          >
            Загрузить в RAG
          </Button>
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-xl font-bold mb-3">Уже загруженные</h3>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-100 text-left">
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
                <tr key={u.id} className="border-t">
                  <td className="p-3">{u.original_name}</td>
                  <td className="p-3 text-xs text-gray-500">{u.mime_type || '—'}</td>
                  <td className="p-3">{u.size ? `${Math.round(u.size / 1024)} КБ` : '—'}</td>
                  <td className="p-3">{u.chunks_count}</td>
                  <td className="p-3">
                    {u.tags && u.tags.length > 0 ? (
                      <div className="flex gap-1 flex-wrap">
                        {u.tags.map((t, i) => (
                          <span key={i} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">{t}</span>
                        ))}
                      </div>
                    ) : '—'}
                  </td>
                  <td className="p-3">{u.uploaded_by || '—'}</td>
                  <td className="p-3 space-x-2">
                    <button
                      onClick={() => download(u)}
                      className="text-blue-600 hover:underline inline-flex items-center gap-1"
                      disabled={!u.mime_type}
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
                  <td colSpan={6} className="p-6 text-center text-gray-500">
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