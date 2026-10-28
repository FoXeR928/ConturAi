import { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { Sidebar } from '../features/chat/Sidebar';
import { ChatWindow } from '../features/chat/ChatWindow';
import { chatsApi, aiApi, Chat, Message } from '../api/chats';
import { useToast } from '../components/ToastContext';

const PAGE_SIZE = 50;

export function ChatPage({ userName, onLogout }: { userName: string; onLogout: () => void; }) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [totalMessages, setTotalMessages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  
  const { toast } = useToast();
  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  // ==========================================================================
  // ЗАГРУЗКА СПИСКА ЧАТОВ
  // ==========================================================================

  const loadChats = async () => {
    try {
      const data = await chatsApi.getChats();
      if (data.result) setChats(data.chats || []);
    } catch (e: any) {
      toast('Не удалось загрузить список чатов', 'error');
    }
  };

  useEffect(() => { loadChats(); }, []);

  // ==========================================================================
  // ЗАГРУЗКА СООБЩЕНИЙ (ПАГИНАЦИЯ)
  // ==========================================================================

  const loadMessages = async (chatId: string) => {
    setActiveChat(chatId);
    setMessages([]);
    setTotalMessages(0);
    
    try {
      // Грузим последние 50 сообщений (offset=0, limit=50)
      const data = await chatsApi.getMessages(chatId, PAGE_SIZE, 0);
      if (data.result) {
        setMessages(data.messages_history || []);
        setTotalMessages(data.total_count || 0);
      }
    } catch (e: any) {
      toast(e.message, 'error');
      setActiveChat(null);
    }
  };

  // Подгрузка старых сообщений (вызывается из ChatWindow)
  const loadMoreMessages = async () => {
    if (!activeChat || loadingMore) return;
    
    // Вычисляем, сколько уже загружено
    const currentOffset = messages.length;
    if (currentOffset >= totalMessages) return; // Все загружено
    
    setLoadingMore(true);
    try {
      const data = await chatsApi.getMessages(activeChat, PAGE_SIZE, currentOffset);
      if (data.result && data.messages_history.length > 0) {
        // Добавляем старые сообщения в НАЧАЛО списка
        setMessages(prev => [...data.messages_history, ...prev]);
      }
    } catch (e: any) {
      toast('Ошибка загрузки старых сообщений', 'error');
    } finally {
      setLoadingMore(false);
    }
  };

  // ==========================================================================
  // СОЗДАНИЕ И ОТПРАВКА
  // ==========================================================================

  const createChat = async () => {
    const name = prompt('Введите название нового чата:');
    if (!name || !name.trim()) return;
    try {
      const data = await chatsApi.createChat(name.trim());
      if (data.result && data.chat_id) {
        await loadChats();
        loadMessages(data.chat_id);
      }
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  const sendMessage = async (text: string, tags: string[], useStream: boolean) => {
    if (!activeChat) return;
    
    // Оптимистично добавляем сообщение пользователя
    setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'user', text }]);
    setLoading(true);

    if (useStream) {
      setMessages((prev) => [...prev, { id: 'stream', chat_role: 'assistant', text: '' }]);
      try {
        await aiApi.askAiStream(
          activeChat, text, tags,
          (chunk) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastIdx = newMessages.length - 1;
              if (newMessages[lastIdx].chat_role === 'assistant') {
                newMessages[lastIdx] = { ...newMessages[lastIdx], text: newMessages[lastIdx].text + chunk };
              }
              return newMessages;
            });
          },
          (error) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1].text = `Ошибка: ${error}`;
              return newMessages;
            });
          }
        );
      } catch (e: any) {
        setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: `Ошибка: ${e.message}` }]);
      } finally {
        setLoading(false);
        loadChats();
      }
    } else {
      try {
        const res = await aiApi.askAi(activeChat, text, tags);
        if (res.result) {
          setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: res.answer }]);
        } else {
          setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: res.message || 'Ошибка' }]);
        }
      } catch (e: any) {
        setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: `Ошибка: ${e.message}` }]);
      } finally {
        setLoading(false);
        loadChats();
      }
    }
  };

  const handleChatDeleted = async () => {
    try {
      const data = await chatsApi.getChats();
      if (data.result) {
        setChats(data.chats || []);
        if (activeChat && !data.chats.some((c: Chat) => c.id === activeChat)) {
          setActiveChat(null);
          setMessages([]);
        }
      }
    } catch (e: any) {
      loadChats();
    }
  };

  return (
    <Layout
      sidebar={<Sidebar chats={chats} activeChatId={activeChat} onSelectChat={loadMessages} onCreateChat={createChat} onLogout={onLogout} isAdmin={isAdmin} onChatDeleted={handleChatDeleted} />}
      header={<Header userName={userName} isAdmin={isAdmin} onLogout={onLogout} />}
    >
      {activeChat ? (
        <ChatWindow
          messages={messages}
          onSendMessage={sendMessage}
          loading={loading}
          chatId={activeChat}
          onRefresh={() => loadMessages(activeChat)}
          onLoadMore={loadMoreMessages}
          hasMore={messages.length < totalMessages}
          loadingMore={loadingMore}
        />
      ) : (
        <div className="flex flex-col h-full items-center justify-center text-gray-400 bg-gray-50/50">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-4xl">💬</span>
          </div>
          <p className="text-lg font-medium text-gray-500">Выберите чат слева</p>
          <p className="text-sm text-gray-400 mt-1">или создайте новый, чтобы начать диалог</p>
        </div>
      )}
    </Layout>
  );
}