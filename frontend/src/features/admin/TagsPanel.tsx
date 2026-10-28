import { useEffect, useState } from 'react';
import { tagsApi, TagItem } from '../../api/tags';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Trash2, Plus, Tag, RefreshCw } from 'lucide-react';
import { useToast } from '../../components/ToastContext';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function TagsPanel() {
  // Используем типизированный массив вместо any[]
  const [tags, setTags] = useState<TagItem[]>([]);
  
  // Поля формы
  const [newName, setNewName] = useState('');
  const [newColor, setNewColor] = useState('#3b82f6');
  
  // Состояния загрузки (для кнопок)
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const { toast } = useToast();

  // ==========================================================================
  // БЛОК 2: ЗАГРУЗКА СПИСКА ТЕГОВ
  // ==========================================================================

  const load = async () => {
    try {
      const data = await tagsApi.getTags();
      setTags(data.tags || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ==========================================================================
  // БЛОК 3: СОЗДАНИЕ НОВОГО ТЕГА
  // ==========================================================================

  const create = async () => {
    if (!newName.trim()) return;
    
    setLoading(true);
    try {
      await tagsApi.createTag(newName.trim(), newColor);
      toast('Тег успешно создан', 'success');
      
      // Очищаем поле ввода
      setNewName('');
      
      // Обновляем только локальное состояние (без запроса к серверу)
      // Так интерфейс работает быстрее.
      await load(); 
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // ==========================================================================
  // БЛОК 4: УДАЛЕНИЕ ТЕГА
  // ==========================================================================

  const remove = async (id: string) => {
    if (!confirm('Удалить этот тег? Он исчезнет из всех чатов и документов.')) return;
    
    setDeletingId(id); // Запоминаем, какой именно тег сейчас удаляется
    try {
      await tagsApi.deleteTag(id);
      toast('Тег удален', 'success');
      
      // Мгновенно убираем тег из списка на экране
      setTags(prev => prev.filter(t => t.id !== id));
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setDeletingId(null);
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <Tag size={24} className="text-blue-600" /> Управление тегами
      </h2>
      
      <p className="text-sm text-gray-500 mb-6">
        Теги помогают пользователям фильтровать документы в базе знаний во время диалога с нейросетью.
      </p>

      {/* ======================================================================
          ФОРМА СОЗДАНИЯ ТЕГА
          ====================================================================== */}
      <div className="bg-white rounded-lg shadow border border-gray-100 p-5 mb-6 flex flex-col md:flex-row md:items-end gap-4">
        
        {/* Название */}
        <div className="flex-1 w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">Название тега</label>
          <Input 
            value={newName} 
            onChange={(e) => setNewName(e.target.value)} 
            placeholder="Например: Бухгалтерия" 
            leftIcon={<Tag size={16} />} 
            onKeyDown={(e) => e.key === 'Enter' && create()}
          />
        </div>
        
        {/* Выбор цвета */}
        <div className="w-full md:w-auto">
          <label className="block text-sm font-medium text-gray-700 mb-1">Цвет</label>
          <div className="flex items-center gap-2 border rounded-lg p-1 bg-gray-50 h-[42px]">
            <input 
              type="color" 
              value={newColor} 
              onChange={(e) => setNewColor(e.target.value)} 
              className="h-8 w-10 cursor-pointer rounded border-0 p-0 bg-transparent" 
            />
            <span className="text-xs font-mono text-gray-500 pr-2 hidden sm:inline">{newColor}</span>
          </div>
        </div>
        
        {/* Кнопка */}
        <Button 
          onClick={create} 
          disabled={loading || !newName.trim()} 
          className="h-[42px] w-full md:w-auto"
        >
          {loading ? <RefreshCw size={18} className="mr-1 animate-spin"/> : <Plus size={18} className="mr-1"/>}
          {loading ? 'Добавление...' : 'Добавить'}
        </Button>
      </div>

      {/* ======================================================================
          ТАБЛИЦА С ТЕГАМИ
          ====================================================================== */}
      <div className="bg-white rounded-lg shadow border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-left border-b">
              <tr>
                <th className="p-3">Тег (внешний вид)</th>
                <th className="p-3">HEX-код</th>
                <th className="p-3 w-24 text-center">Действия</th>
              </tr>
            </thead>
            <tbody>
              {tags.map((t) => {
                const isDeleting = deletingId === t.id;
                return (
                  <tr key={t.id} className="border-t hover:bg-gray-50 transition-colors">
                    <td className="p-3">
                      <span 
                        className="px-3 py-1.5 rounded-md text-white text-xs font-medium shadow-sm inline-block" 
                        style={{ backgroundColor: t.color }}
                      >
                        {t.name}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-xs text-gray-500">{t.color}</td>
                    <td className="p-3 text-center">
                      <button 
                        onClick={() => remove(t.id)} 
                        disabled={isDeleting}
                        className="text-red-500 hover:text-red-700 hover:bg-red-50 p-1.5 rounded transition-colors disabled:opacity-50 inline-flex items-center gap-1"
                        title="Удалить тег"
                      >
                        {isDeleting ? <RefreshCw size={14} className="animate-spin" /> : <Trash2 size={14}/>}
                        {isDeleting ? 'Удаление' : 'Удалить'}
                      </button>
                    </td>
                  </tr>
                );
              })}
              
              {/* Пустое состояние */}
              {tags.length === 0 && !loading && (
                <tr>
                  <td colSpan={3} className="p-8 text-center text-gray-500">
                    <Tag size={32} className="mx-auto mb-2 text-gray-300" />
                    Список тегов пуст. Добавьте первый тег выше.
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