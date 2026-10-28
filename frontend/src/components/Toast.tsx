import { useEffect } from 'react';
import { CheckCircle, AlertTriangle, X } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ (TYPESCRIPT INTERFACES)
// ==============================================================================

export interface ToastData {
  id: number;                   // Уникальный ID (нужен, если выводим несколько тостов одновременно)
  message: string;              // Текст уведомления
  type: 'success' | 'error';    // Тип (влияет на цвет и иконку)
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ TOAST
// ==============================================================================

export function Toast({ toast, onClose }: { toast: ToastData; onClose: () => void }) {
  
  // ==========================================================================
  // БЛОК 3: АВТОМАТИЧЕСКОЕ ЗАКРЫТИЕ (ТАЙМЕР)
  // ==========================================================================
  
  useEffect(() => {
    // Уведомление исчезает через 3.5 секунды (3500 мс)
    const timer = setTimeout(onClose, 3500);
    
    // Если компонент размонтируется раньше (например, пользователь закрыл вручную),
    // очищаем таймер, чтобы избежать утечек памяти и ошибок.
    return () => clearTimeout(timer);
  }, [onClose]);

  const isSuccess = toast.type === 'success';

  return (
    // ==========================================================================
    // БЛОК 4: РЕНДЕР УВЕДОМЛЕНИЯ
    // ==========================================================================
    // fixed bottom-6 right-6 — фиксирует тост в правом нижнем углу экрана.
    // z-50 — гарантирует, что тост будет поверх всех остальных элементов (включая модалки).
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl text-white animate-in slide-in-from-bottom-5 fade-in duration-300 ${
        isSuccess ? 'bg-green-600' : 'bg-red-600'
      }`}
      role="alert" // Для скринридеров (доступность)
    >
      {/* Иконка: Галочка для успеха, Треугольник для ошибки */}
      {isSuccess ? <CheckCircle size={20} className="shrink-0" /> : <AlertTriangle size={20} className="shrink-0" />}
      
      {/* Текст уведомления */}
      <span className="text-sm font-medium">{toast.message}</span>
      
      {/* Кнопка ручного закрытия */}
      <button 
        onClick={onClose} 
        className="ml-2 opacity-70 hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-black/20"
        aria-label="Закрыть уведомление"
      >
        <X size={16} />
      </button>
    </div>
  );
}