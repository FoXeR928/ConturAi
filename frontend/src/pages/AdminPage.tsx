import { useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { usePlugins } from '../plugins/PluginContext';
import { PluginRenderer } from '../plugins/PluginRenderer';
import { UsersPanel } from '../features/admin/UsersPanel';

export function AdminPage({ userName, onLogout }: { userName: string; onLogout: () => void }) {
  const [activeTab, setActiveTab] = useState('users');
  const { plugins } = usePlugins();

  const coreTabs = [{ id: 'users', label: 'Пользователи' }];
  
  const pluginTabs = plugins
    .filter(p => p.frontend_admin_tab)
    .map(p => ({ id: p.id, label: p.frontend_admin_tab!.label, url: p.frontend_admin_tab!.component_url }));

  const allTabs = [...coreTabs, ...pluginTabs];

  return (
    <Layout
      sidebar={
        <div className="p-4 flex flex-col h-full">
          <h1 className="font-bold text-lg mb-6">ConturAI Admin</h1>
          <div className="space-y-1 flex-1">
            {allTabs.map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${activeTab === t.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'}`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <button onClick={onLogout} className="text-gray-400 hover:text-white mt-4 text-sm text-left">Выйти</button>
        </div>
      }
      header={
        // Используем Header для навигации
        <Header userName={userName} isAdmin={true} onLogout={onLogout} />
      }
    >
      <div className="p-6 h-full overflow-y-auto">
        {activeTab === 'users' && <UsersPanel />}
        
        {pluginTabs.map(tab => 
          activeTab === tab.id ? <PluginRenderer key={tab.id} url={tab.url} /> : null
        )}
      </div>
    </Layout>
  );
}