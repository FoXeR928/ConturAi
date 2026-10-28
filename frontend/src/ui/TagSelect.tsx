import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, X } from 'lucide-react';
import { tagsApi, TagItem } from '../api/tags';

// ==============================================================================
// БЛОК 1: ТИПИЗАЦИЯ
// ==============================================================================

interface TagSelectProps {
  /** Массив названий выбранных тегов */
  selected: string[];
  /** Коллбэк при изменении выбора */
  onChange: (tags: string[]) => void;
  placeholder?: string;
  /** Направление открытия списка (вниз для страниц, вверх для полей внизу экрана) */
  direction?: 'up' | 'down';
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ
// ==============================================================================

export function TagSelect({ 
  selected, 
  onChange, 
  placeholder = 'Выбрать теги...',
  direction = 'down',
}: TagSelectProps) {
  const [allTags, setAllTags] = useState<TagItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // ==========================================================================
  // БЛОК 3: ЗАГРУЗКА ТЕГОВ И ОБРАБОТКА КЛИКОВ ВНЕ
  // ==========================================================================

  useEffect(() => {
    tagsApi.getTags()
      .then(data => setAllTags(data.tags || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ==========================================================================
  // БЛОК 4: ДЕЙСТВИЯ
  // ==========================================================================

  const toggleTag = (tagName: string) => {
    onChange(
      selected.includes(tagName) 
        ? selected.filter(t => t !== tagName) 
        : [...selected, tagName]
    );
  };

  // Динамические классы для позиционирования меню
  const dropdownPositionClass = direction === 'up' 
    ? 'bottom-full mb-2' 
    : 'top-full mt-1';

  // ==========================================================================
  // БЛОК 5: РЕНДЕР
  // ==========================================================================

  return (
    <div className="flex flex-wrap items-center gap-2" ref={dropdownRef}>
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-700 min-w-[180px] justify-between transition-colors focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <span>
            {placeholder} {selected.length > 0 && `(${selected.length})`}
          </span>
          <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className={`absolute left-0 w-64 bg-white border rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto ${dropdownPositionClass}`}>
            {allTags.length === 0 ? (
              <div className="p-3 text-gray-500 text-sm text-center">
                Нет доступных тегов.
                <br />
                <span className="text-xs">Попросите администратора их создать.</span>
              </div>
            ) : (
              allTags.map(tag => (
                <div 
                  key={tag.id}
                  onClick={() => toggleTag(tag.name)}
                  className="flex items-center justify-between px-3 py-2.5 hover:bg-gray-50 cursor-pointer text-sm border-b last:border-0"
                >
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: tag.color }} />
                    <span className="font-medium text-gray-700">{tag.name}</span>
                  </div>
                  {selected.includes(tag.name) && <Check size={16} className="text-blue-600" />}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Выбранные теги в виде чипсов */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.map(t => {
            const tagInfo = allTags.find(tag => tag.name === t);
            return (
              <span 
                key={t} 
                className="text-xs px-2.5 py-1 rounded-full text-white flex items-center gap-1 shadow-sm font-medium"
                style={{ backgroundColor: tagInfo?.color || '#3b82f6' }}
              >
                {t}
                <button 
                  type="button" 
                  onClick={() => toggleTag(t)} 
                  className="hover:bg-black/20 rounded-full p-0.5 ml-0.5"
                >
                  <X size={12} />
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}