import { useEffect, useState } from 'react';
import { pluginsApi } from '../api/plugins';
import { PluginSettingsForm } from '../components/PluginSettingsForm';
import type { PluginView } from '../types/plugin';

export function PluginsPage() {
  const [plugins, setPlugins] = useState<PluginView[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    pluginsApi
      .list()
      .then(setPlugins)
      .catch((err: unknown) =>
        setError(
          err instanceof Error ? err.message : 'Ошибка загрузки',
        ),
      )
      .finally(() => setIsLoading(false));
  }, []);

  const handleUpdate = (updated: PluginView): void => {
    setPlugins((prev) =>
      prev.map((p) =>
        p.manifest.id === updated.manifest.id ? updated : p,
      ),
    );
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">
            Плагины
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Управление встроенными и внешними модулями системы.
          </p>
        </header>

        {isLoading && (
          <p className="text-sm text-slate-500">Загрузка...</p>
        )}

        {error && (
          <div className="rounded-lg bg-rose-50 border border-rose-200
                          p-4 text-sm text-rose-700">
            {error}
          </div>
        )}

        {!isLoading && plugins.length === 0 && !error && (
          <div className="rounded-lg bg-white border border-slate-200
                          p-8 text-center text-slate-500 text-sm">
            Нет зарегистрированных плагинов.
          </div>
        )}

        {plugins.map((plugin) => (
          <PluginSettingsForm
            key={plugin.manifest.id}
            plugin={plugin}
            onChange={handleUpdate}
          />
        ))}
      </div>
    </div>
  );
}