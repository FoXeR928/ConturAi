import { useEffect, useState } from 'react';
import { pluginsApi, PluginInfo } from '../../api/plugins';
import { useToast } from '../../components/ToastContext';
import { Puzzle } from 'lucide-react';

export function PluginsPanel() {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState<string | null>(null);
  const { toast } = useToast();

  const load = async () => {
    try {
      const data = await pluginsApi.getPlugins();
      setPlugins(data.plugins || []);
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  useEffect(() => { load(); }, []);

  const toggle = async (p: PluginInfo) => {
    setLoading(p.id);
    try {
      await pluginsApi.togglePlugin(p.id, !p.is_enabled);
      toast(`Плагин "${p.name}" ${!p.is_enabled ? 'включен' : 'выключен'}`, 'success');
      await load();
    } catch (e: any) {
      toast(e.message, 'error');
    } finally {
      setLoading(null);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Puzzle size={24} className="text-blue-600" /> Плагины
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plugins.map(p => (
          <div key={p.id} className="bg-white rounded-lg shadow p-4 border border-gray-100">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-bold text-gray-800">{p.name}</h3>
                <p className="text-xs text-gray-500 font-mono">v{p.version} • {p.type}</p>
              </div>
              <button
                onClick={() => toggle(p)}
                disabled={loading === p.id}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  p.is_enabled ? 'bg-blue-600' : 'bg-gray-300'
                } ${loading === p.id ? 'opacity-50' : ''}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  p.is_enabled ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
            <p className="text-sm text-gray-600">{p.description}</p>
          </div>
        ))}
      </div>

      {plugins.length === 0 && (
        <div className="text-center text-gray-500 mt-10">
          Плагины не найдены. Добавьте их в папку ./plugins
        </div>
      )}
    </div>
  );
}