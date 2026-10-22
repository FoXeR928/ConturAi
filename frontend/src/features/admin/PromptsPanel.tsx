import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Button } from '../../ui/Button';

interface Prompt {
  key: string;
  value: string;
  description: string;
}

const AVAILABLE_VARS: Record<string, { var: string; about: string }[]> = {
  ai_name: [],
  system_prompt: [
    { var: '{name}', about: 'Имя нейросети (из промта ai_name)' },
    { var: '{context}', about: 'Найденные фрагменты документов из RAG' },
  ],
  user_prompt: [
    { var: '{quest}', about: 'Вопрос пользователя' },
    { var: '{context}', about: 'Фрагменты документов (если перенесли сюда)' },
  ],
};

export function PromptsPanel() {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await api.getPrompts();
      setPrompts(data.prompts || []);
      setEditing(
        Object.fromEntries((data.prompts || []).map((p: Prompt) => [p.key, p.value]))
      );
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const save = async (key: string) => {
    try {
      await api.updatePrompt(key, editing[key]);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Промты</h2>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-900">
        <div className="font-semibold mb-2">Доступные переменные</div>
        <p className="mb-2">
          В тексте промта можно использовать фигурные скобки — приложение подставит значения:
        </p>
        <ul className="list-disc list-inside space-y-1">
          <li>
            <code className="bg-blue-100 px-1 rounded">{'{name}'}</code> — имя
            нейросети (значение из промта <code>ai_name</code>). Доступно в{' '}
            <b>system_prompt</b>.
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">{'{context}'}</code> — найденные
            фрагменты документов из базы (RAG). Доступно в <b>system_prompt</b> и{' '}
            <b>user_prompt</b>.
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">{'{quest}'}</code> — вопрос
            пользователя. Доступно в <b>user_prompt</b>.
          </li>
        </ul>
        <p className="mt-2 text-xs text-blue-700">
          Рекомендуется держать <b>{'{context}'}</b> в <b>system_prompt</b>, а в{' '}
          <b>user_prompt</b> — только вопрос. Так модель не путает инструкции с данными.
        </p>
      </div>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="space-y-4">
        {prompts.map((p) => (
          <div key={p.key} className="bg-white rounded-lg shadow p-4">
            <div className="mb-2">
              <div className="font-mono text-sm font-semibold">{p.key}</div>
              <div className="text-xs text-gray-500">{p.description}</div>
              {AVAILABLE_VARS[p.key]?.length > 0 && (
                <div className="text-xs text-gray-400 mt-1">
                  Доступно:{' '}
                  {AVAILABLE_VARS[p.key].map((v, i) => (
                    <span key={v.var}>
                      <code className="bg-gray-100 px-1 rounded">{v.var}</code>
                      {i < AVAILABLE_VARS[p.key].length - 1 ? ', ' : ''}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <textarea
              className="w-full border rounded p-2 font-mono text-sm"
              rows={p.key === 'user_prompt' ? 4 : 10}
              value={editing[p.key] ?? ''}
              onChange={(e) => setEditing({ ...editing, [p.key]: e.target.value })}
            />
            <div className="mt-2 text-right">
              <Button onClick={() => save(p.key)}>Сохранить</Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}