import { useState, KeyboardEvent } from 'react';
import { X } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ТИПИЗАЦИЯ
// ==============================================================================

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ
// ==============================================================================

export function TagInput({ tags, onChange, placeholder = 'Добавить тег...' }: TagInputProps) {
  const [input, setInput] = useState('');

  // ==========================================================================
  // БЛОК 3: ОБРАБОТКА ВВОДА (ENTER, ЗАПЯТАЯ, BACKSPACE)
  // ==========================================================================

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    // Добавление тега по Enter или запятой
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      
      // Очищаем от пробелов и приводим к нижнему регистру
      const newTag = input.trim().toLowerCase();
      
      // Проверяем: тег не пустой и его еще нет в списке
      if (newTag && !tags.includes(newTag)) {
        onChange([...tags, newTag]);
      }
      
      setInput('');
    } 
    // Удаление последнего тега при пустом инпуте (как в Gmail)
    else if (e.key === 'Backspace' && !input && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  };

  const removeTag = (index: number) => {
    onChange(tags.filter((_, i) => i !== index));
  };

  // ==========================================================================
  // БЛОК 4: РЕНДЕР
  // ==========================================================================

  return (
    <div 
      className="flex flex-wrap gap-1.5 p-2 border border-gray-300 rounded-lg bg-white transition-all 
                 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20"
    >
      {/* Отрисовка выбранных тегов */}
      {tags.map((tag, i) => (
        <span 
          key={i} 
          className="flex items-center gap-1.5 bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md text-xs font-medium shadow-sm"
        >
          {tag}
          <button 
            type="button" // <-- Защита от отправки формы при клике
            onClick={() => removeTag(i)} 
            className="hover:text-red-600 hover:bg-blue-200 rounded-full p-0.5 transition-colors"
            aria-label={`Удалить тег ${tag}`}
          >
            <X size={12} />
          </button>
        </span>
      ))}

      {/* Поле ввода */}
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="flex-1 min-w-[120px] outline-none text-sm bg-transparent placeholder:text-gray-400"
      />
    </div>
  );
}