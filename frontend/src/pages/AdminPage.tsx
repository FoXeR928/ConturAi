import { useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { AppSidebar } from '../components/AppSidebar';
import { usePlugins } from '../plugins/PluginContext';
import { PluginRenderer } from '../plugins/PluginRenderer';
import { UsersPanel } from '../features/admin/UsersPanel';

export function AdminPage({ userName, onLogout }: { userName: string; onLogout: () => void }) {
  const [activeTab, setActiveTab] = useState('users');
  const { plugins } = usePlugins();

  // Формируем список вкладок (ядро + плагины)
  const coreTabs = [{ id: 'users', label: 'Пользователи' }];
  const pluginTabs = plugins
    .filter(p => p.frontend_admin_tab)
    .map(p => ({ 
      id: p.id, 
      label: p.frontend_admin_tab!.label, 
      url: p.frontend_admin_tab!.component_url 
    }));

  const allTabs = [...coreTabs, ...pluginTabs];

  return (
    <Layout
      sidebar={
        <AppSidebar
          userName={userName}
          isAdmin={true}
          onLogout={onLogout}
          chats={[]} // В админке чаты не нужны
          activeChatId={null}
          onSelectChat={() => {}}
          onCreateChat={() => {}}
          adminTabs={allTabs}
          activeAdminTab={activeTab}
          onSelectAdminTab={setActiveTab}
        />
      }
      header={<Header userName={userName} isAdmin={true} onLogout={onLogout} />}
    >
      <div className="p-6 h-full overflow-y-auto">
        {/* Рендер базовой вкладки */}
        {activeTab === 'users' && <UsersPanel />}
        
        {/* Рендер вкладок плагинов */}
        {pluginTabs.map(tab => 
          activeTab === tab.id ? <PluginRenderer key={tab.id} url={tab.url} /> : null
        )}
      </div>
    </Layout>
  );
}