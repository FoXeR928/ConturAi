import { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { Header } from '../components/Header';
import { Sidebar } from '../features/chat/Sidebar';
import { ChatWindow } from '../features/chat/ChatWindow';
import { chatsApi, aiApi, Chat, Message } from '../api/chats';
import { useToast } from '../components/ToastContext';

// ==============================================================================
// БЛОК 1: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function ChatPage({ userName, onLogout }: { userName: string; onLogout: () => void; }) {
  // Используем типизированные массивы вместо any[]
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  
  const { toast } = useToast();
  
  // Проверяем статус админа для сайдбара и шапки
  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  // ==========================================================================
  // БЛОК 2: ЗАГРУЗКА ДАННЫХ (ЧАТЫ И СООБЩЕНИЯ)
  // ==========================================================================

  const loadChats = async () => {
    try {
      const data = await chatsApi.getChats();
      if (data.result) setChats(data.chats || []);
    } catch (e: any) {
      toast('Не удалось загрузить список чатов', 'error');
    }
  };

  useEffect(() => { 
    loadChats(); 
  }, []);

  const loadMessages = async (chatId: string) => {
    setActiveChat(chatId);
    try {
      const data = await chatsApi.getMessages(chatId);
      if (data.result) setMessages(data.messages_history || []);
    } catch (e: any) {
      toast(e.message, 'error');
      // Если чат не загрузился (например, его удалили), сбрасываем активный чат
      setActiveChat(null); 
      setMessages([]);
    }
  };

  // ==========================================================================
  // БЛОК 3: СОЗДАНИЕ НОВОГО ЧАТА
  // ==========================================================================

  const createChat = async () => {
    const name = prompt('Введите название нового чата:');
    if (!name || !name.trim()) return;
    
    try {
      const data = await chatsApi.createChat(name.trim());
      if (data.result && data.chat_id) {
        await loadChats(); // Обновляем список в сайдбаре
        loadMessages(data.chat_id); // Переключаемся на новый чат
      }
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  // ==========================================================================
  // БЛОК 4: ОТПРАВКА СООБЩЕНИЯ (С ПОДДЕРЖКОЙ СТРИМИНГА)
  // ==========================================================================

  const sendMessage = async (text: string, tags: string[], useStream: boolean) => {
    if (!activeChat) return;
    
    // 1. Мгновенно добавляем сообщение пользователя в интерфейс
    setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'user', text }]);
    setLoading(true);

    if (useStream) {
      // --- ВЕТКА СТРИМИНГА ---
      // Добавляем пустое сообщение ассистента, которое будем наполнять
      setMessages((prev) => [...prev, { id: 'stream', chat_role: 'assistant', text: '' }]);
      
      try {
        await aiApi.askAiStream(
          activeChat,
          text,
          tags,
          // Коллбэк при получении нового кусочка текста
          (chunk) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastIdx = newMessages.length - 1;
              if (newMessages[lastIdx].chat_role === 'assistant') {
                newMessages[lastIdx] = {
                  ...newMessages[lastIdx],
                  text: newMessages[lastIdx].text + chunk,
                };
              }
              return newMessages;
            });
          },
          // Коллбэк при ошибке
          (error) => {
            setMessages((prev) => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1].text = `⚠️ Ошибка: ${error}`;
              return newMessages;
            });
          }
        );
      } catch (e: any) {
        setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: `⚠️ Ошибка: ${e.message}` }]);
      } finally {
        setLoading(false);
        loadChats(); // Обновляем сайдбар (там может обновиться дата последнего сообщения)
      }
    } else {
      // --- ВЕТКА ПОЛНОГО ОТВЕТА ---
      try {
        const res = await aiApi.askAi(activeChat, text, tags);
        if (res.result) {
          setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: res.answer }]);
        } else {
          setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: `⚠️ ${res.message || 'Неизвестная ошибка'}` }]);
        }
      } catch (e: any) {
        setMessages((prev) => [...prev, { id: Date.now().toString(), chat_role: 'assistant', text: `⚠️ Ошибка: ${e.message}` }]);
      } finally {
        setLoading(false);
        loadChats();
      }
    }
  };

  // ==========================================================================
  // БЛОК 5: ОБРАБОТКА УДАЛЕНИЯ/ПЕРЕИМЕНОВАНИЯ ЧАТА
  // ==========================================================================

  const handleChatDeleted = async () => {
    try {
      const data = await chatsApi.getChats();
      if (data.result) {
        setChats(data.chats || []);
        
        // Если удалили активный чат — сбрасываем окно сообщений
        if (activeChat) {
          const stillExists = data.chats.some((c: Chat) => c.id === activeChat);
          if (!stillExists) {
            setActiveChat(null);
            setMessages([]);
          }
        }
      }
    } catch (e: any) {
      // При ошибке просто перезагружаем список
      loadChats();
    }
  };

  const handleRefreshMessages = () => {
    if (activeChat) loadMessages(activeChat);
  };

  // ==========================================================================
  // БЛОК 6: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

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
          onSendMessage={sendMessage}
          loading={loading}
          chatId={activeChat}
          onRefresh={handleRefreshMessages}
        />
      ) : (
        // Заглушка, если чат не выбран
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