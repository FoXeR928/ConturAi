import {
  createContext,
  useCallback,
  useContext,
  useState,
  ReactNode,
  useRef,
} from 'react';

type ToastKind = 'error' | 'success' | 'info';

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  show: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastContextValue>({ show: () => undefined });

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const show = useCallback(
    (message: string, kind: ToastKind = 'info') => {
      const id = ++idRef.current;
      setToasts((prev) => [...prev, { id, kind, message }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    },
    [],
  );

  const colors: Record<ToastKind, string> = {
    error: 'bg-rose-600',
    success: 'bg-emerald-600',
    info: 'bg-slate-800',
  };

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2
                      max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-3 rounded-lg shadow-lg text-white
                        text-sm ${colors[t.kind]}`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = (): ToastContextValue => useContext(ToastContext);