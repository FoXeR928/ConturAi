import { useEffect, useState } from 'react';
import { fewShotsApi, FewShotExample } from '../../api/fewShots';
import { Button } from '../../ui/Button';
import { useToast } from '../../components/ToastContext';
import { Brain, Plus, Trash2, RefreshCw } from 'lucide-react';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function FewShotsPanel() {
  // Используем типизированный массив вместо any[]
  const [examples, setExamples] = useState<FewShotExample[]>([]);
  
  // Поля формы
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // ==========================================================================
  // БЛОК 2: ЗАГРУЗКА ДАННЫХ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await fewShotsApi.getExamples();
      setExamples(data.examples || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => { 
    load(); 
  }, []);

  // ==========================================================================
  // БЛОК 3: ДОБАВЛЕНИЕ НОВОГО ПРИМЕРА
  // ==========================================================================

  const add = async () => {
    if (!question.trim() || !answer.trim()) return;
    
    setLoading(true);
    try {
      await fewShotsApi.createExample(question, answer);
      toast('Пример успешно добавлен', 'success');
      
      // Очищаем поля после успешного добавления
      setQuestion('');
      setAnswer('');
      
      await load(); // Обновляем таблицу
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================================
  // БЛОК 4: УДАЛЕНИЕ ПРИМЕРА
  // ==========================================================================

  const remove = async (id: string) => {
    if (!confirm('Удалить этот пример? Нейросеть перестанет использовать его в ответах.')) return;
    
    try {
      await fewShotsApi.deleteExample(id);
      toast('Пример удален', 'success');
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      {/* Заголовок */}
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Brain size={24} className="text-purple-600" /> База знаний (Few-Shot)
      </h2>
      
      {/* Информационная плашка */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-900">
        <p className="leading-relaxed">
          Нейросеть будет брать <b>3 случайных примера</b> отсюда и подмешивать их в системный промт. 
          Это помогает ИИ отвечать в нужном стиле, соблюдать формат (например, таблицы) и не галлюцинировать по частым вопросам.
        </p>
      </div>

      {/* Форма добавления */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="bg-white rounded-lg shadow p-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Вопрос пользователя
          </label>
          <textarea
            className="w-full border rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow"
            rows={4}
            placeholder="Например: Сколько дней отпуска у сварщика?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Идеальный ответ
          </label>
          <textarea
            className="w-full border rounded p-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow"
            rows={4}
            placeholder="Например: 28 дней основного + 7 дней за вредность. [Инструкция_по_охране_труда.pdf]"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
        </div>
      </div>
      
      {/* Кнопка добавления */}
      <div className="flex justify-end mb-8">
        <Button 
          onClick={add} 
          disabled={loading || !question.trim() || !answer.trim()} 
          className="flex items-center gap-2"
        >
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Plus size={16} />}
          {loading ? 'Добавление...' : 'Добавить пример'}
        </Button>
      </div>

      {/* Таблица с существующими примерами */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[600px]">
            <thead className="bg-gray-100 text-left border-b">
              <tr>
                <th className="p-3 w-1/3">Вопрос</th>
                <th className="p-3 w-1/2">Ответ</th>
                <th className="p-3 w-16 text-center">Действия</th>
              </tr>
            </thead>
            <tbody>
              {examples.map((e) => (
                <tr key={e.id} className="border-t hover:bg-gray-50 transition-colors">
                  <td className="p-3 font-medium text-gray-800">{e.question}</td>
                  <td className="p-3 text-gray-600 whitespace-pre-wrap">{e.answer}</td>
                  <td className="p-3 text-center">
                    <button 
                      onClick={() => remove(e.id)} 
                      className="text-red-500 hover:text-red-700 p-1.5 rounded hover:bg-red-50 transition-colors"
                      title="Удалить"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              
              {examples.length === 0 && (
                <tr>
                  <td colSpan={3} className="p-8 text-center text-gray-500">
                    Примеров пока нет. Добавьте первый, чтобы улучшить качество ответов!
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