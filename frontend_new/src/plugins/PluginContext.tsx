import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getToken } from '../api/http';

export interface PluginInfo {
  id: string;
  name: string;
  // Ссылки на JS-файлы компонентов (если плагин предоставляет UI)
  frontend_chat_button?: string;
  frontend_admin_tab?: { label: string; component_url: string };
}

interface PluginContextType {
  plugins: PluginInfo[];
  isLoading: boolean;
}

const PluginContext = createContext<PluginContextType>({ plugins: [], isLoading: true });

export function PluginProvider({ children }: { children: ReactNode }) {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadPlugins = async () => {
      try {
        // Запрашиваем у бэкенда (эндпоинт /api/plugins/active) список плагинов
        const res = await fetch('/api/plugins/active', {
          headers: { Authorization: `Bearer ${getToken()}` }
        });
        const data = await res.json();
        // Здесь бэкенд должен вернуть полные метаданные плагинов (включая URL фронтенд-модулей)
        setPlugins(data.plugins || []);
      } catch (e) {
        console.error("Ошибка загрузки плагинов", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadPlugins();
  }, []);

  return (
    <PluginContext.Provider value={{ plugins, isLoading }}>
      {children}
    </PluginContext.Provider>
  );
}

export const usePlugins = () => useContext(PluginContext);