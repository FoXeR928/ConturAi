import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { Sidebar } from '../features/chat/Sidebar';
import { ChatWindow } from '../features/chat/ChatWindow';

export function ChatPage({
  userName,
  onLogout,
}: {
  userName: string;
  onLogout: () => void;
}) {
  const [chats, setChats] = useState<any[]>([]);
  const [activeChat, setActiveChat] = useState<number | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  const loadChats = async () => {
    const data = await api.getChats();
    if (data.result) setChats(data.chats);
  };

  useEffect(() => {
    loadChats();
  }, []);

  const loadMessages = async (chatId: number) => {
    setActiveChat(chatId);
    const data = await api.getMessages(chatId);
    if (data.result) setMessages(data.messages_history);
  };

  const createChat = async () => {
    const name = prompt('Название чата:');
    if (!name) return;
    const data = await api.createChat(name);
    if (data.result) {
      await loadChats();
      loadMessages(data.chat_id);
    }
  };

  const sendMessage = async (text: string) => {
    if (!activeChat) return;
    setMessages((prev) => [...prev, { chat_role: 'user', text }]);
    setLoading(true);
    try {
      const res = await api.askAi(activeChat, text);
      if (res.result) {
        setMessages((prev) => [...prev, { chat_role: 'assistant', text: res.answer }]);
      } else {
        setMessages((prev) => [
          ...prev,
          { chat_role: 'assistant', text: res.message || 'Ошибка' },
        ]);
      }
    } catch (e: any) {
      setMessages((prev) => [...prev, { chat_role: 'assistant', text: `Ошибка: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout
      sidebar={
        <Sidebar
          chats={chats}
          activeChatId={activeChat}
          onSelectChat={loadMessages}
          onCreateChat={createChat}
          onLogout={onLogout}
          isAdmin={isAdmin}
        />
      }
      header={<Header userName={userName} isAdmin={isAdmin} onLogout={onLogout} />}
    >
      {activeChat ? (
        <ChatWindow messages={messages} onSendMessage={sendMessage} loading={loading} />
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          Выберите чат или создайте новый
        </div>
      )}
    </Layout>
  );
}