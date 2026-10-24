import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { llmConfigsApi } from '../../api/llmConfigs';

interface LlmConfig {
  key: string;
  value: string;
  description: string;
  input_type: string;
}

const GROUPS: { title: string; keys: string[] }[] = [
  {
    title: 'Подключение к vLLM',
    keys: ['vllm_base_url', 'vllm_api_key', 'vllm_model_name'],
  },
  {
    title: 'Генерация (Sampling)',
    keys: [
      'vllm_temperature',
      'vllm_max_tokens',
      'vllm_top_p',
      'vllm_top_k',
      'vllm_presence_penalty',
      'vllm_frequency_penalty',
      'vllm_seed',
    ],
  },
  {
    title: 'Поиск по документам (RAG)',
    keys: [
      'rag_search_limit',
      'rag_chunk_size',
      'rag_chunk_overlap',
      'rag_batch_size',
    ],
  },
  {
    title: 'Безопасность (JWT)',
    keys: ['token_expire_minutes', 'token_expire_days'],
  },
];

export function LlmConfigsPanel() {
  const [configs, setConfigs] = useState<LlmConfig[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [savedKey, setSavedKey] = useState<string | null>(null);

  const load = async () => {
    try {
      const data = await llmConfigsApi.getLlmConfigs();
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
    setError('');
    try {
      await llmConfigsApi.updateLlmConfig(key, editing[key]);
      setSavedKey(key);
      setTimeout(() => setSavedKey(null), 2000);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const grouped = GROUPS.map((g) => ({
    title: g.title,
    items: configs.filter((c) => g.keys.includes(c.key)),
  }));
  const knownKeys = new Set(GROUPS.flatMap((g) => g.keys));
  const others = configs.filter((c) => !knownKeys.has(c.key));
  if (others.length > 0) {
    grouped.push({ title: 'Другие настройки', items: others });
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Параметры LLM</h2>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-900">
        <div className="font-semibold mb-1">Как это работает</div>
        <ul className="list-disc list-inside space-y-1">
          <li>
            Все параметры сохраняются в БД и применяются к <b>следующему</b> запросу
            в чат. Перезапуск контейнеров не нужен.
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">rag_chunk_size</code> и{' '}
            <code className="bg-blue-100 px-1 rounded">rag_chunk_overlap</code>{' '}
            влияют только на <b>новые</b> загруженные документы. Старые остаются
            нарезанными по-прежнему — перезагрузите их, если хотите применить.
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">token_expire_*</code> влияют
            только на <b>новые</b> токены. Уже выданные работают до истечения.
          </li>
        </ul>
      </div>

      {grouped.map(
        (group) =>
          group.items.length > 0 && (
            <section
              key={group.title}
              className="bg-white rounded-lg shadow p-4 mb-4"
            >
              <h3 className="font-semibold text-lg mb-4 text-gray-800">
                {group.title}
              </h3>
              <div className="space-y-4">
                {group.items.map((c) => {
                  const isNumber = c.input_type === 'number' || c.input_type === 'float';
                  return (
                    <div
                      key={c.key}
                      className="border-b pb-3 last:border-none last:pb-0"
                    >
                      <div className="mb-1">
                        <div className="font-mono text-sm font-semibold">
                          {c.key}
                        </div>
                        <div className="text-xs text-gray-500">
                          {c.description}
                        </div>
                      </div>
                      <div className="flex gap-2 items-center">
                        <Input
                          type={isNumber ? 'number' : 'text'}
                          step={
                            c.input_type === 'float'
                              ? '0.01'
                              : c.input_type === 'number'
                              ? '1'
                              : undefined
                          }
                          value={editing[c.key] ?? ''}
                          onChange={(e) =>
                            setEditing({ ...editing, [c.key]: e.target.value })
                          }
                        />
                        <Button onClick={() => save(c.key)}>
                          {savedKey === c.key ? '✓' : 'Сохранить'}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )
      )}

      <p className="text-sm text-gray-500 mt-3">
        Параметры читаются из БД на каждый запрос — изменения видны сразу.
        Флаги запуска vLLM (<code>--max-model-len</code>,{' '}
        <code>--gpu-memory-utilization</code>) меняются через{' '}
        <code>docker compose restart vllm</code> и живут в <code>.env</code>.
      </p>
    </div>
  );
}