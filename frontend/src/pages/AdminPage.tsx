import { useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';

// Импорт всех панелей
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
import { TagsPanel } from '../features/admin/TagsPanel';

// Импорт иконок для меню
import { 
  Users, Terminal, Settings, FileText, Trash, Tag, 
  Database, Brain, Download, Activity, ClipboardList 
} from 'lucide-react';

// ==============================================================================
// БЛОК 1: ОПИСАНИЕ ТИПОВ И КОНФИГУРАЦИЯ ВКЛАДОК
// ==============================================================================

type Tab = 
  | 'users' | 'prompts' | 'llm' | 'docs' | 'chats' | 'tags' 
  | 'system' | 'downloads' | 'audit' | 'few-shots' | 'database';

// Конфигурация меню: связываем ID вкладки, читаемое название и иконку
const TABS: { id: Tab; label: string; icon: any }[] = [
  { id: 'users', label: 'Пользователи', icon: Users },
  { id: 'prompts', label: 'Промты', icon: Terminal },
  { id: 'llm', label: 'Параметры LLM', icon: Settings },
  { id: 'docs', label: 'Документы', icon: FileText },
  { id: 'tags', label: 'Теги', icon: Tag },
  { id: 'chats', label: 'Корзина чатов', icon: Trash },
  { id: 'database', label: 'Базы данных', icon: Database },
  { id: 'few-shots', label: 'База знаний (Few-Shot)', icon: Brain },
  { id: 'downloads', label: 'Запросы на скачивание', icon: Download },
  { id: 'audit', label: 'Журнал событий', icon: ClipboardList },
  { id: 'system', label: 'Мониторинг', icon: Activity },
];

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ СТРАНИЦЫ
// ==============================================================================

export function AdminPage({ userName, onLogout }: { userName?: string; onLogout: () => void; }) {
  // Состояние активной вкладки (по умолчанию — Пользователи)
  const [tab, setTab] = useState<Tab>('users');

  return (
    <Layout
      // ========================================================================
      // БЛОК 3: БОКОВОЕ МЕНЮ (SIDEBAR)
      // ========================================================================
      sidebar={
        <div className="flex flex-col h-full bg-gray-900 text-white">
          {/* Заголовок админки */}
          <div className="p-5 border-b border-gray-800 shrink-0">
            <div className="text-xl font-bold tracking-wide text-gray-100 flex items-center gap-2">
              ConturAI
            </div>
            <div className="text-xs text-gray-500 mt-1 uppercase font-semibold tracking-wider">
              Панель управления
            </div>
          </div>

          {/* Навигация */}
          <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin scrollbar-thumb-gray-700">
            {TABS.map((t) => {
              const Icon = t.icon;
              const isActive = tab === t.id;
              
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    isActive 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                  }`}
                >
                  <Icon size={18} className={isActive ? 'text-white' : 'text-gray-500'} />
                  {t.label}
                </button>
              );
            })}
          </div>
        </div>
      }
      
      // ========================================================================
      // БЛОК 4: ШАПКА
      // ========================================================================
      header={<Header userName={userName} isAdmin onLogout={onLogout} />}
    >
      
      {/* ======================================================================
          БЛОК 5: ОБЛАСТЬ КОНТЕНТА (РЕНДЕР ПАНЕЛЕЙ)
          ====================================================================== */}
      <div className="h-full overflow-y-auto p-4 sm:p-6 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          {tab === 'users' && <UsersPanel />}
          {tab === 'prompts' && <PromptsPanel />}
          {tab === 'llm' && <LlmConfigsPanel />}
          {tab === 'docs' && <DocsPanel />}
          {tab === 'tags' && <TagsPanel />}
          {tab === 'chats' && <DeletedChatsPanel />}
          {tab === 'database' && <DatabasePanel />}
          {tab === 'few-shots' && <FewShotsPanel />}
          {tab === 'downloads' && <DownloadRequestsPanel />}
          {tab === 'audit' && <AuditPanel />}
          {tab === 'system' && <SystemStatsPanel />}
        </div>
      </div>
    </Layout>
  );
}