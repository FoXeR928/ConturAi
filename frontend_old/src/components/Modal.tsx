import { ReactNode, useEffect } from 'react';
import { X } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ТИПИЗАЦИЯ И ИНТЕРФЕЙС
// ==============================================================================

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  
  // ==========================================================================
  // БЛОК 2: UX-УЛУЧШЕНИЯ (ESC И БЛОКИРОВКА СКРОЛЛА)
  // ==========================================================================
  
  useEffect(() => {
    // 1. Закрытие по нажатию Escape
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);

    // 2. Блокировка прокрутки основного контента под модалкой
    // Запоминаем текущий overflow и ставим hidden
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    // Очистка при закрытии модалки
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = originalOverflow;
    };
  }, [onClose]);

  return (
    // ==========================================================================
    // БЛОК 3: ФОН (BACKDROP)
    // ==========================================================================
    // fixed inset-0 — растягивает на весь экран.
    // z-50 — кладет поверх всего остального интерфейса.
    // bg-black/40 — полупрозрачный черный фон.
    // backdrop-blur-sm — добавляет легкое размытие (эффект стекла).
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={onClose} // Клик по фону закрывает модалку
    >
      
      {/* ========================================================================
          БЛОК 4: ОКНО МОДАЛКИ
          ========================================================================
          stopPropagation нужен, чтобы клик ВНУТРИ окна не всплывал до фона 
          и не закрывал модалку (иначе форму невозможно будет заполнить).
          max-h-[90vh] — ограничивает высоту окна, чтобы оно не вылезло за экран.
      */}
      <div 
        className="bg-white rounded-xl shadow-2xl w-full max-w-lg flex flex-col max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()} 
        role="dialog"
        aria-modal="true"
      >
        
        {/* 4.1. Шапка модалки */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50/50 shrink-0">
          <h3 className="font-semibold text-lg text-gray-800">{title}</h3>
          <button 
            onClick={onClose} 
            className="p-1 rounded-md text-gray-500 hover:text-gray-800 hover:bg-gray-200 transition-colors"
            aria-label="Закрыть"
          >
            <X size={20} />
          </button>
        </div>

        {/* 4.2. Контент (скроллится независимо) */}
        <div className="p-4 overflow-y-auto">
          {children}
        </div>
        
      </div>
    </div>
  );
}