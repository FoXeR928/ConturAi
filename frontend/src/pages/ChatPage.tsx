import { useState, useEffect } from 'react';
import { Layout } from '../components/Layout';
import { chatsApi, Chat } from '../api/chats';
import { usePlugins } from '../plugins/PluginContext';
import { PluginRenderer } from '../plugins/PluginRenderer';
import { getToken } from '../api/http';
import { Button } from '../ui/Button';
import { ChatWindow } from '../features/chat/ChatWindow'; // <-- Импорт

export function ChatPage({ onLogout }: { onLogout: () => void }) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const { plugins } = usePlugins();

  const loadChats = () => chatsApi.getChats().then(data => setChats(data.chats || []));

  useEffect(() => { loadChats(); }, []);

  return (
    <Layout
      sidebar={
        <div className="p-4 flex flex-col h-full">
          <h1 className="font-bold text-lg mb-4">ConturAI</h1>
          <Button onClick={async () => {
            const name = prompt("Имя чата:");
            if (name) {
              const res = await chatsApi.createChat(name);
              loadChats();
              setActiveChat(res.chat_id);
            }
          }} className="mb-4">Новый чат</Button>
          
          <div className="flex-1 overflow-y-auto space-y-1">
            {chats.map(c => (
              <div key={c.id} onClick={() => setActiveChat(c.id)} className={`p-2 rounded cursor-pointer ${activeChat === c.id ? 'bg-gray-800' : 'hover:bg-gray-800'}`}>
                {c.name}
              </div>
            ))}
          </div>
          <button onClick={onLogout} className="text-gray-400 hover:text-white mt-4 text-sm text-left">Выйти</button>
        </div>
      }
      header={
        <div className="h-14 flex items-center justify-between px-6 bg-white border-b border-gray-200 shrink-0">
          <span className="font-medium">Чат</span>
          <div className="flex gap-2">
            {plugins.filter(p => p.frontend_chat_button).map(p => (
              <PluginRenderer key={p.id} url={p.frontend_chat_button!} props={{ chatId: activeChat, token: getToken() }} />
            ))}
          </div>
        </div>
      }
    >
      {activeChat ? (
        <ChatWindow chatId={activeChat} /> // <-- Используем компонент
      ) : (
        <div className="flex h-full items-center justify-center text-gray-400">
          Выберите чат или создайте новый
        </div>
      )}
    </Layout>
  );
}