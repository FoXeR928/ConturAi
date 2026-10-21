import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';

interface LlmConfig {
  key: string;
  value: string;
  description: string;
  input_type: string;
}

export function LlmConfigsPanel() {
  const [configs, setConfigs] = useState<LlmConfig[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await api.getLlmConfigs();
      setConfigs(data.configs || []);
      setEditing(
        Object.fromEntries((data.configs || []).map((c: LlmConfig) => [c.key, c.value]))
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
      await api.updateLlmConfig(key, editing[key]);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Параметры LLM</h2>
      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}
      <div className="bg-white rounded-lg shadow p-4 space-y-4">
        {configs.map((c) => (
          <div key={c.key} className="border-b pb-3 last:border-none last:pb-0">
            <div className="mb-1">
              <div className="font-mono text-sm font-semibold">{c.key}</div>
              <div className="text-xs text-gray-500">{c.description}</div>
            </div>
            <div className="flex gap-2">
              <Input
                type={c.input_type === 'number' ? 'number' : 'text'}
                step={c.input_type === 'float' ? '0.1' : undefined}
                value={editing[c.key] ?? ''}
                onChange={(e) => setEditing({ ...editing, [c.key]: e.target.value })}
              />
              <Button onClick={() => save(c.key)}>Сохранить</Button>
            </div>
          </div>
        ))}
      </div>
      <p className="text-sm text-gray-500 mt-3">
        Изменения применяются к следующему запросу в чат без перезапуска контейнеров.
      </p>
    </div>
  );
}