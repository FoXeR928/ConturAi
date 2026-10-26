import { useEffect, useState } from 'react';
import { fewShotsApi } from '../../api/fewShots';
import { Button } from '../../ui/Button';
import { useToast } from '../../components/ToastContext';
import { Brain, Plus, Trash2 } from 'lucide-react';

export function FewShotsPanel() {
  const [examples, setExamples] = useState<any[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const load = async () => {
    try {
      const data = await fewShotsApi.getExamples();
      setExamples(data.examples || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!question.trim() || !answer.trim()) return;
    setLoading(true);
    try {
      await fewShotsApi.createExample(question, answer);
      toast('Пример успешно добавлен', 'success');
      setQuestion('');
      setAnswer('');
      load();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: string) => {
    if (!confirm('Удалить этот пример?')) return;
    try {
      await fewShotsApi.deleteExample(id);
      toast('Пример удален', 'success');
      load();
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Brain size={24} /> База знаний (Few-Shot)
      </h2>
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm text-blue-900">
        <p>
          Нейросеть будет брать <b>3 случайных примера</b> отсюда и подмешивать их в системный промт. 
          Это помогает ИИ отвечать в нужном стиле и не галлюцинировать по частым вопросам.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Вопрос пользователя</label>
          <textarea
            className="w-full border rounded p-2 text-sm"
            rows={4}
            placeholder="Например: Сколько дней отпуска у сварщика?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Идеальный ответ</label>
          <textarea
            className="w-full border rounded p-2 text-sm"
            rows={4}
            placeholder="Например: 28 дней основного + 7 дней за вредность. [Инструкция_по_охране_труда.pdf]"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
          />
        </div>
      </div>
      
      <div className="flex justify-end mb-8">
        <Button onClick={add} disabled={loading || !question || !answer} className="flex items-center gap-2">
          <Plus size={16} /> {loading ? 'Добавление...' : 'Добавить пример'}
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-3 w-1/3">Вопрос</th>
              <th className="p-3 w-1/2">Ответ</th>
              <th className="p-3 w-16">Действия</th>
            </tr>
          </thead>
          <tbody>
            {examples.map((e) => (
              <tr key={e.id} className="border-t">
                <td className="p-3 font-medium text-gray-800">{e.question}</td>
                <td className="p-3 text-gray-600">{e.answer}</td>
                <td className="p-3">
                  <button 
                    onClick={() => remove(e.id)} 
                    className="text-red-600 hover:text-red-800"
                    title="Удалить"
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {examples.length === 0 && (
              <tr>
                <td colSpan={3} className="p-6 text-center text-gray-500">
                  Примеров пока нет. Добавьте первый!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}