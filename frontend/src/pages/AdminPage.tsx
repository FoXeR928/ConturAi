import { useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { UsersPanel } from '../features/admin/UsersPanel';
import { PromptsPanel } from '../features/admin/PromptsPanel';
import { LlmConfigsPanel } from '../features/admin/LlmConfigsPanel';
import { DocsPanel } from '../features/admin/DocsPanel';

type Tab = 'users' | 'prompts' | 'llm' | 'docs';

const TABS: { id: Tab; label: string }[] = [
  { id: 'users', label: 'Пользователи' },
  { id: 'prompts', label: 'Промты' },
  { id: 'llm', label: 'Параметры LLM' },
  { id: 'docs', label: 'Документы' },
];

export function AdminPage({
  userName,
  onLogout,
}: {
  userName?: string;
  onLogout: () => void;
}) {
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
                  tab === t.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800'
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
      </div>
    </Layout>
  );
}