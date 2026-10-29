import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { AppSidebar } from '../components/AppSidebar';
import { chatsApi, Chat } from '../api/chats';
import { usePlugins } from '../plugins/PluginContext';
import { PluginRenderer } from '../plugins/PluginRenderer';
import { getToken } from '../api/http';
import { ChatWindow } from '../features/chat/ChatWindow';

interface ChatPageProps {
  userName: string;
  isAdmin: boolean;
  onLogout: () => void;
}

export function ChatPage({ userName, isAdmin, onLogout }: ChatPageProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const { plugins } = usePlugins();

  const loadChats = () => chatsApi.getChats().then(data => setChats(data.chats || []));

  useEffect(() => { loadChats(); }, []);

  const handleCreateChat = async () => {
    const name = prompt("Имя чата:");
    if (name) {
      const res = await chatsApi.createChat(name);
      loadChats();
      setActiveChat(res.chat_id);
    }
  };

  return (
    <Layout
      sidebar={
        <AppSidebar
          userName={userName}
          isAdmin={isAdmin}
          onLogout={onLogout}
          chats={chats}
          activeChatId={activeChat}
          onSelectChat={setActiveChat}
          onCreateChat={handleCreateChat}
        />
      }
      header={
        <Header userName={userName} isAdmin={isAdmin} onLogout={onLogout}>
          {/* СЛОТ ДЛЯ КНОПОК ПЛАГИНОВ В ШАПКЕ */}
          {plugins.filter(p => p.frontend_chat_button).map(p => (
            <PluginRenderer 
              key={p.id} 
              url={p.frontend_chat_button!} 
              props={{ chatId: activeChat, token: getToken() }} 
            />
          ))}
        </Header>
      }
    >
      {activeChat ? (
        <ChatWindow chatId={activeChat} /> 
      ) : (
        <div className="flex h-full items-center justify-center text-gray-400 bg-gray-50/50">
          Выберите чат или создайте новый
        </div>
      )}
    </Layout>
  );
}