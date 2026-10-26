import { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { Sidebar } from '../features/chat/Sidebar';
import { ChatWindow } from '../features/chat/ChatWindow';
import { chatsApi, streamAiMessage } from '../api/chats';

export function ChatPage({ userName, onLogout }: { userName: string; onLogout: () => void; }) {
  const [chats, setChats] = useState<any[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  const loadChats = async () => {
    const data = await chatsApi.getChats();
    if (data.result) setChats(data.chats);
  };

  useEffect(() => { loadChats(); }, []);

  const loadMessages = async (chatId: string) => {
    setActiveChat(chatId);
    const data = await chatsApi.getMessages(chatId);
    if (data.result) setMessages(data.messages_history);
  };

  const createChat = async () => {
    const name = prompt('Название чата:');
    if (!name) return;
    const data = await chatsApi.createChat(name);
    if (data.result) {
      await loadChats();
      loadMessages(data.chat_id);
    }
  };

  // ОБНОВЛЕНО: принимаем теги
  const sendMessage = async (text: string, tags: string[] = []) => {
    if (!activeChat || loading) return;
    
    setMessages((prev) => [
      ...prev, 
      { chat_role: 'user', text },
      { chat_role: 'assistant', text: '' } 
    ]);
    setLoading(true);

    try {
      // ОБНОВЛЕНО: передаем теги в стриминг
      await streamAiMessage(
        activeChat,
        text,
        tags,
        (chunk) => {
          setMessages((prev) => {
            const newArr = [...prev];
            newArr[newArr.length - 1] = {
              ...newArr[newArr.length - 1],
              text: newArr[newArr.length - 1].text + chunk,
            };
            return newArr;
          });
        },
        () => setLoading(false)
      );
    } catch (e: any) {
      setMessages((prev) => {
        const newArr = [...prev];
        newArr[newArr.length - 1] = {
          ...newArr[newArr.length - 1],
          text: `Ошибка: ${e.message}`,
        };
        return newArr;
      });
      setLoading(false);
    }
  };

  const handleChatDeleted = async () => {
    if (activeChat) {
      const data = await chatsApi.getChats();
      if (data.result) {
        const stillExists = data.chats.some((c: any) => c.id === activeChat);
        if (!stillExists) {
          setActiveChat(null);
          setMessages([]);
        }
        setChats(data.chats);
      }
    } else {
      loadChats();
    }
  };

  const handleRefreshMessages = () => {
    if (activeChat) loadMessages(activeChat);
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
          onChatDeleted={handleChatDeleted}
        />
      }
      header={<Header userName={userName} isAdmin={isAdmin} onLogout={onLogout} />}
    >
      {activeChat ? (
        <ChatWindow
          messages={messages}
          onSendMessage={sendMessage} // Передаем обновленную функцию
          loading={loading}
          chatId={activeChat}
          onRefresh={handleRefreshMessages}
        />
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          Выберите чат или создайте новый
        </div>
      )}
    </Layout>
  );
}