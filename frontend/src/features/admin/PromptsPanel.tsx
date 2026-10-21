import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Button } from '../../ui/Button';

interface Prompt {
  key: string;
  value: string;
  description: string;
}

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
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}
      <div className="space-y-4">
        {prompts.map((p) => (
          <div key={p.key} className="bg-white rounded-lg shadow p-4">
            <div className="mb-2">
              <div className="font-mono text-sm font-semibold">{p.key}</div>
              <div className="text-xs text-gray-500">{p.description}</div>
            </div>
            <textarea
              className="w-full border rounded p-2 font-mono text-sm"
              rows={5}
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