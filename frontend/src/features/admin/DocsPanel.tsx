import { useRef, useState } from 'react';
import { api } from '../../api/client';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Upload, FileText } from 'lucide-react';

export function DocsPanel() {
  const [name, setName] = useState('');
  const [text, setText] = useState('');
  const [fileText, setFileText] = useState('');
  const [file, setFile] = useState<string>('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);

  const readFile = async (f: File) => {
    setError('');
    setFile(f.name);
    try {
      const data = await api.readDoc(f);
      if (data.result) {
        setFileText(data.file_text);
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
      const data = await api.addDoc(name || file, text || fileText);
      setSuccess(data.message);
      setName('');
      setText('');
      setFileText('');
      setFile('');
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
            <Upload size={18} /> Файл
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
    </div>
  );
}