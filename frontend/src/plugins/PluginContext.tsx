import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { pluginsApi, PluginItem } from '../api/plugins';

interface PluginContextType {
  plugins: PluginItem[];
  refreshPlugins: () => Promise<void>;
  isLoading: boolean;
}

const PluginContext = createContext<PluginContextType>({ plugins: [], refreshPlugins: async () => {}, isLoading: true });

export function PluginProvider({ children }: { children: ReactNode }) {
  const [plugins, setPlugins] = useState<PluginItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    try {
      const data = await pluginsApi.getActivePlugins();
      setPlugins(data.plugins || []);
    } catch (e) {
      console.error("Ошибка загрузки плагинов", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <PluginContext.Provider value={{ plugins, refreshPlugins: load, isLoading }}>
      {children}
    </PluginContext.Provider>
  );
}

export const usePlugins = () => useContext(PluginContext);