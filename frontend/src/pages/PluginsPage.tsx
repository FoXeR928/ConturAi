import { useEffect, useState } from 'react';
import { pluginsApi } from '../api/plugins';
import { ApiError } from '../api/http';
import { PluginSettingsForm } from '../components/PluginSettingsForm';
import { useToast } from '../components/ToastProvider';
import type { PluginView } from '../types/plugin';

export function PluginsPage() {
  const [plugins, setPlugins] = useState<PluginView[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showRegister, setShowRegister] = useState(false);
  const [endpointUrl, setEndpointUrl] = useState('');
  const [manifestJson, setManifestJson] = useState('');
  const [registering, setRegistering] = useState(false);
  const { show } = useToast();

  const load = async (): Promise<void> => {
    try {
      setPlugins(await pluginsApi.list());
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка загрузки',
        'error',
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const handleUpdate = (updated: PluginView): void => {
    setPlugins((prev) =>
      prev.map((p) =>
        p.manifest.id === updated.manifest.id ? updated : p,
      ),
    );
  };

  const handleRegister = async (): Promise<void> => {
    setRegistering(true);
    try {
      const manifest = JSON.parse(manifestJson) as Record<string, unknown>;
      const created = await pluginsApi.register({
        manifest,
        endpoint_url: endpointUrl.trim(),
      });
      handleUpdate(created);
      show(`Плагин "${created.manifest.name}" подключён`, 'success');
      setShowRegister(false);
      setEndpointUrl('');
      setManifestJson('');
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
          ? err.message
          : 'Ошибка регистрации';
      show(message, 'error');
    } finally {
      setRegistering(false);
    }
  };

  const handleDelete = async (plugin: PluginView): Promise<void> => {
    if (!confirm(`Отключить плагин "${plugin.manifest.name}"?`)) return;
    try {
      await pluginsApi.remove(plugin.manifest.id);
      setPlugins((prev) =>
        prev.filter((p) => p.manifest.id !== plugin.manifest.id),
      );
      show('Плагин удалён', 'success');
    } catch (err) {
      show(
        err instanceof ApiError ? err.message : 'Ошибка удаления',
        'error',
      );
    }
  };

  const sorted = [...plugins].sort(
    (a, b) => a.manifest.priority - b.manifest.priority,
  );

  const activePipelines = sorted.filter((p) => p.manifest.is_active);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              Плагины
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Пайплайн:{' '}
              {activePipelines.length === 0 ? (
                <span className="text-rose-600">пусто</span>
              ) : (
                <span className="font-mono text-slate-700">
                  {activePipelines
                    .map((p) => p.manifest.name)
                    .join(' → ')}
                </span>
              )}
            </p>
          </div>
          <button
            onClick={() => setShowRegister((v) => !v)}
            className="px-4 py-2 rounded-lg bg-slate-900 text-white
                       text-sm font-medium hover:bg-slate-800"
          >
            {showRegister ? 'Отмена' : '+ Подключить внешний'}
          </button>
        </header>

        {showRegister && (
          <div className="bg-white rounded-lg border border-slate-200
                          shadow-sm p-6 space-y-4">
            <h2 className="text-sm font-semibold text-slate-900">
              Подключить внешний плагин
            </h2>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-600">
                Endpoint URL
              </label>
              <input
                value={endpointUrl}
                onChange={(e) => setEndpointUrl(e.target.value)}
                placeholder="http://my-plugin:8000"
                className="w-full px-3 py-2 rounded-lg border
                           border-slate-300 text-sm font-mono
                           focus:outline-none focus:ring-2
                           focus:ring-indigo-500"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-600">
                Манифест (JSON)
              </label>
              <textarea
                value={manifestJson}
                onChange={(e) => setManifestJson(e.target.value)}
                rows={10}
                placeholder={`{
  "id": "my_plugin",
  "name": "My Plugin",
  "kind": "external",
  "api_version": "1",
  "priority": 50,
  "settings_schema": {}
}`}
                className="w-full px-3 py-2 rounded-lg border
                           border-slate-300 text-xs font-mono
                           focus:outline-none focus:ring-2
                           focus:ring-indigo-500"
              />
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleRegister}
                disabled={
                  registering ||
                  !endpointUrl.trim() ||
                  !manifestJson.trim()
                }
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white
                           text-sm font-medium hover:bg-indigo-700
                           disabled:opacity-60"
              >
                {registering ? 'Подключение...' : 'Подключить'}
              </button>
            </div>
          </div>
        )}

        {isLoading && (
          <p className="text-sm text-slate-500">Загрузка...</p>
        )}

        {!isLoading && sorted.length === 0 && (
          <div className="rounded-lg bg-white border border-slate-200
                          p-8 text-center text-slate-500 text-sm">
            Нет зарегистрированных плагинов. Проверьте папку{' '}
            <code className="font-mono">backend/plugins/</code>.
          </div>
        )}

        {sorted.map((plugin) => (
          <div key={plugin.manifest.id} className="space-y-2">
            <PluginSettingsForm
              plugin={plugin}
              onChange={handleUpdate}
            />
            {plugin.manifest.kind === 'external' && (
              <div className="flex justify-end">
                <button
                  onClick={() => handleDelete(plugin)}
                  className="text-xs text-rose-600 hover:text-rose-700
                             font-medium"
                >
                  Отключить внешний плагин
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}