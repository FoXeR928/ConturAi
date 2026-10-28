import { createContext, useContext, useState, useRef, ReactNode } from 'react';
import { CheckCircle, AlertTriangle, Info, X } from 'lucide-react';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ И КОНТЕКСТА
// ==============================================================================

type ToastType = 'success' | 'error' | 'info';

interface ToastData {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  /** Функция вызова уведомления. */
  toast: (message: string, type?: ToastType) => void;
}

// Создаем контекст. По умолчанию undefined, чтобы хук useToast мог 
// выбросить ошибку, если его используют вне провайдера.
const ToastContext = createContext<ToastContextType | undefined>(undefined);


// ==============================================================================
// БЛОК 2: КОМПОНЕНТ-ПРОВАЙДЕР (ХРАНИЛИЩЕ И РЕНДЕР)
// ==============================================================================

export function ToastProvider({ children }: { children: ReactNode }) {
  // Массив активных уведомлений
  const [toasts, setToasts] = useState<ToastData[]>([]);
  
  // Используем useRef для генерации уникальных ID.
  // Это надежнее, чем Date.now(), так как исключает коллизии,
  // если два тоста вызваны одновременно.
  const toastIdRef = useRef(0);

  // ============================================================================
  // ФУНКЦИЯ ДОБАВЛЕНИЯ УВЕДОМЛЕНИЯ
  // ============================================================================
  
  const toast = (message: string, type: ToastType = 'info') => {
    const id = ++toastIdRef.current;
    
    // Добавляем новый тост в конец массива
    setToasts((prev) => [...prev, { id, message, type }]);
    
    // Устанавливаем таймер на автоматическое удаление через 3.5 секунды
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  };

  // ============================================================================
  // ФУНКЦИЯ РУЧНОГО УДАЛЕНИЯ (ПО КЛИКУ НА КРЕСТИК)
  // ============================================================================
  
  const removeToast = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}

      {/* ======================================================================
          БЛОК 3: КОНТЕЙНЕР ДЛЯ ОТОБРАЖЕНИЯ УВЕДОМЛЕНИЙ
          ======================================================================
          fixed bottom-6 right-6 — прибивает контейнер к правому нижнему углу.
          z-50 — поверх всего интерфейса (включая модальные окна).
          flex-col gap-2 — уведомления выстраиваются друг под другом.
      */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
        {toasts.map((t) => {
          // Определяем цвет фона в зависимости от типа
          const bgColor = 
            t.type === 'success' ? 'bg-green-600' : 
            t.type === 'error' ? 'bg-red-600' : 
            'bg-blue-600';

          return (
            <div
              key={t.id}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-xl text-white transition-all animate-slide-in ${bgColor}`}
              role="alert"
            >
              {/* Иконка, соответствующая типу */}
              {t.type === 'success' && <CheckCircle size={20} className="shrink-0" />}
              {t.type === 'error' && <AlertTriangle size={20} className="shrink-0" />}
              {t.type === 'info' && <Info size={20} className="shrink-0" />}

              {/* Текст уведомления */}
              <span className="text-sm font-medium">{t.message}</span>

              {/* Кнопка закрытия */}
              <button
                onClick={() => removeToast(t.id)}
                className="ml-2 opacity-70 hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-black/20"
                aria-label="Закрыть"
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}


// ==============================================================================
// БЛОК 4: КАСТОМНЫЙ ХУК ДЛЯ УДОБНОГО ВЫЗОВА
// ==============================================================================

export function useToast() {
  const context = useContext(ToastContext);
  
  // Защита от использования хука вне провайдера
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  
  return context;
}