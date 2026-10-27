import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { llmConfigsApi, LlmConfigItem } from '../../api/llmConfigs';
import { RefreshCw, Check } from 'lucide-react';

// ==============================================================================
// БЛОК 1: КОНФИГУРАЦИЯ ГРУПП
// ==============================================================================

// Группируем настройки по смыслу, чтобы админ не терялся в куче параметров.
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
      'vllm_stream',
    ],
  },
  {
    title: 'Лимиты и контекст',
    keys: [
      'vllm_max_model_len',
      'chat_history_limit',
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

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function LlmConfigsPanel() {
  // Типизированный массив конфигов
  const [configs, setConfigs] = useState<LlmConfigItem[]>([]);
  
  // Объект с текущими (редактируемыми) значениями полей
  const [editing, setEditing] = useState<Record<string, string>>({});
  
  const [error, setError] = useState('');
  
  // Состояния для UX (какой параметр сохраняется / только что сохранен)
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  // ==========================================================================
  // БЛОК 3: ЗАГРУЗКА ДАННЫХ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await llmConfigsApi.getLlmConfigs();
      setConfigs(data.configs || []);
      
      // Заполняем форму текущими значениями из БД
      setEditing(
        Object.fromEntries((data.configs || []).map((c: LlmConfigItem) => [c.key, c.value]))
      );
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ==========================================================================
  // БЛОК 4: СОХРАНЕНИЕ ПАРАМЕТРА
  // ==========================================================================

  const save = async (key: string) => {
    setError('');
    setSavingKey(key);
    
    try {
      await llmConfigsApi.updateLlmConfig(key, editing[key]);
      
      // Обновляем локальное состояние, чтобы не вызывать load() и не сбрасывать другие правки
      setConfigs(prev => prev.map(c => c.key === key ? { ...c, value: editing[key] } : c));
      
      setSavedKey(key);
      setTimeout(() => setSavedKey(null), 2000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSavingKey(null);
    }
  };

  // ==========================================================================
  // БЛОК 5: РАСПРЕДЕЛЕНИЕ НАСТРОЕК ПО ГРУППАМ
  // ==========================================================================

  const grouped = GROUPS.map((g) => ({
    title: g.title,
    items: configs.filter((c) => g.keys.includes(c.key)),
  }));
  
  // Все настройки, которых нет в GROUPS, падают в блок "Другие настройки"
  const knownKeys = new Set(GROUPS.flatMap((g) => g.keys));
  const others = configs.filter((c) => !knownKeys.has(c.key));
  if (others.length > 0) {
    grouped.push({ title: 'Другие настройки', items: others });
  }

  // ==========================================================================
  // БЛОК 6: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Параметры LLM</h2>

      {error && <div className="bg-red-50 text-red-600 p-3 rounded mb-4">{error}</div>}

      {/* Информационная плашка */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-900">
        <div className="font-semibold mb-1">Как это работает</div>
        <ul className="list-disc list-inside space-y-1">
          <li>
            Все параметры сохраняются в БД и применяются к <b>следующему</b> запросу в чат. Перезапуск контейнеров не нужен.
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">rag_chunk_size</code> и <code className="bg-blue-100 px-1 rounded">rag_chunk_overlap</code> влияют только на <b>новые</b> загруженные документы.
          </li>
          <li>
            <code className="bg-blue-100 px-1 rounded">token_expire_*</code> влияют только на <b>новые</b> токены.
          </li>
        </ul>
      </div>

      {/* Рендер групп настроек */}
      {grouped.map(
        (group) =>
          group.items.length > 0 && (
            <section key={group.title} className="bg-white rounded-lg shadow p-5 mb-5 border border-gray-100">
              <h3 className="font-semibold text-lg mb-4 text-gray-800 border-b pb-2">
                {group.title}
              </h3>
              
              <div className="space-y-5">
                {group.items.map((c) => {
                  const isNumber = c.input_type === 'number' || c.input_type === 'float';
                  const isBoolean = c.input_type === 'boolean';
                  const isSaving = savingKey === c.key;
                  const isSaved = savedKey === c.key;

                  return (
                    <div key={c.key} className="flex flex-col md:flex-row md:items-center gap-4">
                      
                      {/* Левая часть: Название и описание */}
                      <div className="md:w-1/2">
                        <div className="font-mono text-sm font-semibold text-gray-800">
                          {c.key}
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {c.description}
                        </div>
                      </div>
                      
                      {/* Правая часть: Поле ввода и кнопка */}
                      <div className="flex gap-2 items-center md:w-1/2">
                        
                        {/* Если тип boolean — рисуем чекбокс */}
                        {isBoolean ? (
                          <label className="flex items-center gap-2 cursor-pointer bg-gray-50 px-3 py-2 rounded-lg border flex-1 hover:bg-gray-100 transition-colors">
                            <input
                              type="checkbox"
                              className="w-5 h-5 rounded text-blue-600 focus:ring-blue-500 border-gray-300"
                              checked={editing[c.key] === 'true'}
                              onChange={(e) => setEditing({ ...editing, [c.key]: e.target.checked ? 'true' : 'false' })}
                            />
                            <span className="text-sm text-gray-700 font-medium">
                              {editing[c.key] === 'true' ? 'Включено' : 'Выключено'}
                            </span>
                          </label>
                        ) : (
                          /* Если число или текст — рисуем Input */
                          <Input
                            type={isNumber ? 'number' : 'text'}
                            step={c.input_type === 'float' ? '0.01' : c.input_type === 'number' ? '1' : undefined}
                            value={editing[c.key] ?? ''}
                            onChange={(e) => setEditing({ ...editing, [c.key]: e.target.value })}
                            className="flex-1"
                          />
                        )}
                        
                        <Button 
                          onClick={() => save(c.key)} 
                          disabled={isSaving}
                          className={`w-28 ${isSaved ? 'bg-green-600 hover:bg-green-700' : ''}`}
                        >
                          {isSaving ? (
                            <RefreshCw size={16} className="animate-spin mx-auto" />
                          ) : isSaved ? (
                            <Check size={16} className="mx-auto" />
                          ) : (
                            'Сохранить'
                          )}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          )
      )}

      <p className="text-sm text-gray-500 mt-6 bg-gray-50 p-3 rounded border">
        Параметры читаются из БД на каждый запрос — изменения видны сразу.
        Флаги запуска vLLM (<code>--max-model-len</code>, <code>--gpu-memory-utilization</code>) меняются через <code>docker compose restart vllm</code> и живут в <code>.env</code>.
      </p>
    </div>
  );
}