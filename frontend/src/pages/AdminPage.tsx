import { useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { UsersPanel } from '../features/admin/UsersPanel';
import { PromptsPanel } from '../features/admin/PromptsPanel';
import { LlmConfigsPanel } from '../features/admin/LlmConfigsPanel';
import { DocsPanel } from '../features/admin/DocsPanel';
import { DeletedChatsPanel } from '../features/admin/DeletedChatsPanel';
import { DatabasePanel } from '../features/admin/DatabasePanel';
import { FewShotsPanel } from '../features/admin/FewShotsPanel';
import { SystemStatsPanel } from '../features/admin/SystemStatsPanel';
import { DownloadRequestsPanel } from '../features/admin/DownloadRequestsPanel';
import { AuditPanel } from '../features/admin/AuditPanel';

type Tab = 'users' | 'prompts' | 'llm' | 'docs' | 'chats' | 'system' | 'downloads' | 'audit' | 'few-shots' | 'database';

const TABS: { id: Tab; label: string }[] = [
  { id: 'users', label: 'Пользователи' },
  { id: 'prompts', label: 'Промты' },
  { id: 'llm', label: 'Параметры LLM' },
  { id: 'docs', label: 'Документы' },
  { id: 'chats', label: 'Корзина чатов' },
  { id: 'database', label: 'Базы данных' },
  { id: 'few-shots', label: 'База знаний' },
  { id: 'downloads', label: 'Запросы на скачивание' },
  { id: 'audit', label: 'Журнал событий' },
  { id: 'system', label: 'Мониторинг' },
];

export function AdminPage({ userName, onLogout }: { userName?: string; onLogout: () => void; }) {
  const [tab, setTab] = useState<Tab>('users');

  return (
    <Layout
      sidebar={
        <div className="p-4">
          <div className="text-lg font-bold mb-4">ConturAI</div>
          <div className="space-y-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                  tab === t.id ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      }
      header={<Header userName={userName} isAdmin onLogout={onLogout} />}
    >
      <div className="h-full overflow-y-auto p-6">
        {tab === 'users' && <UsersPanel />}
        {tab === 'prompts' && <PromptsPanel />}
        {tab === 'llm' && <LlmConfigsPanel />}
        {tab === 'docs' && <DocsPanel />}
        {tab === 'chats' && <DeletedChatsPanel />}
        {tab === 'database' && <DatabasePanel />}
        {tab === 'few-shots' && <FewShotsPanel />}
        {tab === 'downloads' && <DownloadRequestsPanel />}
        {tab === 'audit' && <AuditPanel />}
        {tab === 'system' && <SystemStatsPanel />}
      </div>
    </Layout>
  );
}