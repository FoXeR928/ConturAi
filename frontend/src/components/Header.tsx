import { Link, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { LogOut, MessageSquare, Shield } from 'lucide-react';
import { Button } from '../ui/Button';
import { systemApi } from '../api/system';

interface HeaderProps {
  userName?: string;
  isAdmin: boolean;
  onLogout: () => void;
}

export function Header({ userName, isAdmin, onLogout }: HeaderProps) {
  // ==========================================================================
  // БЛОК 1: МОНИТОРИНГ СТАТУСА НЕЙРОСЕТИ
  // ==========================================================================
  
  // null = проверка еще идет, true = онлайн, false = оффлайн
  const [llmOnline, setLlmOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        // Используем централизованный API (он сам подставит нужный URL и токен)
        const data = await systemApi.getVllmStatus();
        setLlmOnline(data.status === 'ok');
      } catch {
        setLlmOnline(false);
      }
    };

    // Проверяем сразу при загрузке
    checkHealth();

    // И далее каждые 10 секунд (чтобы видеть, если сервер упал или перезагрузился)
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  
  // ==========================================================================
  // БЛОК 2: НАВИГАЦИЯ
  // ==========================================================================
  
  const { pathname } = useLocation();
  
  // Вспомогательная функция для рендера вкладки
  const tab = (to: string, label: string, Icon: any) => (
    <Link
      to={to}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        pathname.startsWith(to)
          ? 'bg-blue-600 text-white' // Активная вкладка
          : 'text-gray-600 hover:bg-gray-100' // Неактивная
      }`}
    >
      <Icon size={16} />
      {label}
    </Link>
  );

  
  // ==========================================================================
  // БЛОК 3: РЕНДЕР
  // ==========================================================================
  
  return (
    <header className="h-14 flex items-center justify-between px-6 bg-white border-b border-gray-200">
      {/* Левая часть: Навигация */}
      <div className="flex items-center gap-2">
        {tab('/chat', 'Чаты', MessageSquare)}
        {isAdmin && tab('/admin', 'Администрирование', Shield)}
      </div>

      {/* Правая часть: Статус, Имя и Выход */}
      <div className="flex items-center gap-4">
        
        {/* Индикатор статуса vLLM */}
        <div className="flex items-center gap-2 text-sm text-gray-500" title="Статус нейросети">
          <div className={`w-3 h-3 rounded-full ${
            llmOnline === null ? 'bg-gray-300 animate-pulse' : 
            llmOnline ? 'bg-green-500' : 'bg-red-500'
          }`} />
          
          {llmOnline === false && <span className="text-red-500 font-medium">Оффлайн</span>}
          {llmOnline === true && <span className="text-green-600 font-medium hidden sm:inline">Онлайн</span>}
        </div>

        {/* Имя пользователя */}
        <span className="text-sm font-medium text-gray-700">{userName}</span>

        {/* Кнопка выхода */}
        <Button variant="secondary" onClick={onLogout} className="flex gap-2 items-center">
          <LogOut size={16} /> Выйти
        </Button>
      </div>
    </header>
  );
}