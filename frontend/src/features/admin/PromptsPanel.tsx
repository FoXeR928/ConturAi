import { useEffect, useState } from 'react';
import { Button } from '../../ui/Button';
import { promptsApi, PromptItem } from '../../api/prompts';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';

// ==============================================================================
// БЛОК 1: КОНСТАНТЫ И СПРАВОЧНИКИ
// ==============================================================================

// Справочник доступных переменных для каждого промпта.
// Это помогает админу не забыть, какие плейсхолдеры можно использовать.
const AVAILABLE_VARS: Record<string, { var: string; about: string }[]> = {
  ai_name: [],
  system_prompt: [
    { var: '{name}', about: 'Имя нейросети (из промпта ai_name)' },
    { var: '{context}', about: 'Найденные фрагменты документов из RAG' },
  ],
  user_prompt: [
    { var: '{quest}', about: 'Вопрос пользователя' },
    { var: '{context}', about: 'Фрагменты документов (если перенесли сюда)' },
  ],
};

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function PromptsPanel() {
  const [prompts, setPrompts] = useState<PromptItem[]>([]);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  
  // Состояния для отображения процесса сохранения
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  // ==========================================================================
  // БЛОК 3: ЗАГРУЗКА ДАННЫХ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await promptsApi.getPrompts();
      setPrompts(data.prompts || []);
      
      // Заполняем форму текущими значениями
      setEditing(
        Object.fromEntries((data.prompts || []).map((p: PromptItem) => [p.key, p.value]))
      );
    } catch (e: any) {
      setError(e.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ==========================================================================
  // БЛОК 4: СОХРАНЕНИЕ ПРОМПТА
  // ==========================================================================

  const save = async (key: string) => {
    setError('');
    setSavingKey(key);
    
    try {
      await promptsApi.updatePrompt(key, editing[key]);
      
      // Обновляем локальный стейт, чтобы не перезагружать всю страницу.
      // Это сохраняет фокус и другие несохраненные изменения в соседних полях.
      setPrompts(prev => prev.map(p => p.key === key ? { ...p, value: editing[key] } : p));
      
      setSavedKey(key);
      setTimeout(() => setSavedKey(null), 2000); // Показываем галочку 2 секунды
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSavingKey(null);
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Промпты</h2>

      {/* Информационная плашка с подсказками */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-900 shadow-sm">
        <div className="font-semibold mb-2 flex items-center gap-2">
          <AlertCircle size={16} /> Доступные переменные
        </div>
        <p className="mb-2">
          В тексте промпта можно использовать фигурные скобки — приложение подставит значения:
        </p>
        <ul className="list-disc list-inside space-y-1 ml-1">
          <li>
            <code className="bg-blue-100 px-1.5 py-0.5 rounded font-mono text-xs">{'{name}'}</code> — имя
            нейросети (значение из промпта <code>ai_name</code>). Доступно в <b>system_prompt</b>.
          </li>
          <li>
            <code className="bg-blue-100 px-1.5 py-0.5 rounded font-mono text-xs">{'{context}'}</code> — найденные
            фрагменты документов из базы (RAG). Доступно в <b>system_prompt</b> и <b>user_prompt</b>.
          </li>
          <li>
            <code className="bg-blue-100 px-1.5 py-0.5 rounded font-mono text-xs">{'{quest}'}</code> — вопрос
            пользователя. Доступно в <b>user_prompt</b>.
          </li>
        </ul>
        <p className="mt-3 text-xs text-blue-700 font-medium bg-blue-100/50 p-2 rounded">
          💡 Рекомендуется держать <b>{'{context}'}</b> в <b>system_prompt</b>, а в <b>user_prompt</b> — только вопрос. Так модель не путает инструкции с данными.
        </p>
      </div>

      {/* Блок ошибок */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-lg mb-4 flex items-center gap-2">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Список промптов */}
      <div className="space-y-4">
        {prompts.map((p) => {
          const isSaving = savingKey === p.key;
          const isSaved = savedKey === p.key;

          return (
            <div key={p.key} className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
              <div className="p-4 bg-gray-50/50 border-b border-gray-100">
                <div className="font-mono text-sm font-bold text-gray-800">{p.key}</div>
                <div className="text-xs text-gray-500 mt-1">{p.description}</div>
                
                {/* Отображение доступных переменных для конкретного промпта */}
                {AVAILABLE_VARS[p.key]?.length > 0 && (
                  <div className="text-xs text-gray-500 mt-2 flex flex-wrap gap-1 items-center">
                    <span>Доступно:</span>
                    {AVAILABLE_VARS[p.key].map((v, i) => (
                      <span key={v.var} title={v.about}>
                        <code className="bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded font-mono">{v.var}</code>
                        {i < AVAILABLE_VARS[p.key].length - 1 ? ', ' : ''}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="p-4">
                <textarea
                  className="w-full border rounded-lg p-3 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all resize-y"
                  rows={p.key === 'user_prompt' ? 4 : 10}
                  value={editing[p.key] ?? ''}
                  onChange={(e) => setEditing({ ...editing, [p.key]: e.target.value })}
                  spellCheck={false}
                />
                
                <div className="mt-3 flex justify-end">
                  <Button 
                    onClick={() => save(p.key)} 
                    disabled={isSaving}
                    className={`w-32 flex items-center justify-center transition-colors ${
                      isSaved ? 'bg-green-600 hover:bg-green-700' : ''
                    }`}
                  >
                    {isSaving ? (
                      <><RefreshCw size={16} className="animate-spin mr-2" /> Сохранение</>
                    ) : isSaved ? (
                      <><Check size={16} className="mr-2" /> Сохранено</>
                    ) : (
                      'Сохранить'
                    )}
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}