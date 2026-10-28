import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Trash2, Download, Zap, AlignLeft, MessageSquare, Clock, Loader2 } from 'lucide-react';
import { Input } from '../../ui/Input';
import { Button } from '../../ui/Button';
import { TagSelect } from '../../ui/TagSelect';
import { chatsApi } from '../../api/chats';
import { downloadsApi } from '../../api/downloads';
import { cleanMarkdown } from '../../utils/markdown';
import { useToast } from '../../components/ToastContext';

// ==============================================================================
// БЛОК 1: ТИПИЗАЦИЯ
// ==============================================================================

interface ChatMessage {
  id?: string;
  chat_role: 'user' | 'assistant';
  text: string;
}

interface ChatWindowProps {
  messages: ChatMessage[];
  onSendMessage: (text: string, tags: string[], useStream: boolean) => Promise<void>;
  loading: boolean;
  chatId: string;
  onRefresh: () => void;
  onLoadMore: () => void;
  hasMore: boolean;
  loadingMore: boolean;
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ
// ==============================================================================

export function ChatWindow({ 
  messages, onSendMessage, loading, chatId, onRefresh,
  onLoadMore, hasMore, loadingMore
}: ChatWindowProps) {
  const [input, setInput] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [downloadStatus, setDownloadStatus] = useState<'idle' | 'pending'>('idle');
  
  const [useStream, setUseStream] = useState<boolean>(() => {
    const saved = localStorage.getItem('use_stream');
    return saved !== null ? saved === 'true' : false;
  });

  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const topSentinelRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  // ==========================================================================
  // УМНЫЙ АВТОСКРОЛЛ ВНИЗ (при новых сообщениях)
  // ==========================================================================

  const prevMessagesLength = useRef(messages.length);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    // Если количество сообщений увеличилось НЕ из-за подгрузки старых (в начало),
    // а из-за нового сообщения в конец — скроллим вниз
    const isNewMessage = messages.length > prevMessagesLength.current;
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150;
    
    if (isNewMessage && isNearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    
    prevMessagesLength.current = messages.length;
  }, [messages]);

  // ==========================================================================
  // ИНТЕРСЕКШН-ОБСЕРВЕР ДЛЯ ПОДГРУЗКИ СТАРЫХ СООБЩЕНИЙ
  // ==========================================================================

  useEffect(() => {
    const sentinel = topSentinelRef.current;
    const container = scrollContainerRef.current;
    if (!sentinel || !container) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          onLoadMore();
        }
      },
      { root: container, rootMargin: '100px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, onLoadMore]);

  // ==========================================================================
  // ДЕЙСТВИЯ
  // ==========================================================================

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    
    setInput('');
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    
    await onSendMessage(text, selectedTags, useStream);
  };

  const toggleStream = () => {
    const newVal = !useStream;
    setUseStream(newVal);
    localStorage.setItem('use_stream', String(newVal));
  };

  const handleDeleteMessage = async (msgId: string) => {
    if (!confirm('Удалить сообщение?')) return;
    try {
      await chatsApi.deleteMessage(chatId, msgId);
      onRefresh();
    } catch (err: any) {
      toast(err.message, 'error');
    }
  };

  const handleExport = async () => {
    if (isAdmin) {
      try {
        await chatsApi.exportChat(chatId, `chat_${chatId}.md`);
        toast('Чат успешно экспортирован', 'success');
      } catch (e: any) {
        toast(e.message, 'error');
      }
      return;
    }

    if (downloadStatus === 'pending') {
      toast('Ваш запрос ожидает одобрения администратора', 'info');
      return;
    }

    try {
      await chatsApi.exportChat(chatId, `chat_${chatId}.md`);
      toast('Чат успешно экспортирован', 'success');
    } catch (e: any) {
      if (e.message?.includes('запрещено') || e.message?.includes('доступ')) {
        try {
          await downloadsApi.requestAccess({ chatId });
          setDownloadStatus('pending');
          toast('Запрос на скачивание отправлен администратору', 'success');
        } catch (reqErr: any) {
          if (reqErr.message?.includes('уже создана')) {
            setDownloadStatus('pending');
            toast('Запрос уже в обработке', 'info');
          } else {
            toast(reqErr.message, 'error');
          }
        }
      } else {
        toast(e.message, 'error');
      }
    }
  };

  // ==========================================================================
  // РЕНДЕР
  // ==========================================================================

  return (
    <div className="flex flex-col h-full bg-gray-50/50">
      
      {/* Шапка */}
      <div className="p-4 border-b bg-white flex justify-between items-center shrink-0">
        <h2 className="font-bold text-lg text-gray-800">История диалога</h2>
        <Button 
          variant="secondary" 
          onClick={handleExport} 
          disabled={downloadStatus === 'pending'}
          className="flex items-center gap-2 text-sm px-3 py-1.5 h-auto"
        >
          {downloadStatus === 'pending' ? (
            <><Clock size={16} className="text-yellow-500" /> Ожидание...</>
          ) : (
            <><Download size={16} /> Скачать</>
          )}
        </Button>
      </div>

      {/* Лента сообщений */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6" ref={scrollContainerRef}>
        
        {/* Маркер для загрузки старых сообщений */}
        <div ref={topSentinelRef} className="h-1">
          {loadingMore && (
            <div className="flex justify-center items-center py-4 text-gray-400 text-sm">
              <Loader2 size={20} className="animate-spin mr-2" /> Загрузка истории...
            </div>
          )}
        </div>

        {messages.map((msg, idx) => {
          const isUser = msg.chat_role === 'user';
          const isStreaming = loading && idx === messages.length - 1 && !isUser;

          return (
            <div key={msg.id || idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'} group relative`}>
              <div className={`max-w-[85%] p-4 rounded-2xl ${
                isUser
                  ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-200'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
              }`}>
                {isUser ? (
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                ) : (
                  <div className="prose prose-sm max-w-none prose-table:border prose-table:border-gray-300 prose-th:bg-gray-100 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:px-3 prose-td:py-2 prose-td:border-t prose-td:border-gray-200 prose-pre:bg-gray-800 prose-pre:text-gray-100">
                    {msg.text ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {cleanMarkdown(msg.text)}
                      </ReactMarkdown>
                    ) : (
                      isStreaming && <span className="animate-pulse">▍</span>
                    )}
                  </div>
                )}

                {msg.id && !isStreaming && (
                  <button
                    onClick={() => handleDeleteMessage(msg.id!)}
                    className={`absolute top-2 ${isUser ? '-left-8' : '-right-8'} opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity`}
                    title="Удалить сообщение"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} className="h-4" />
      </div>

      {/* Панель ввода */}
      <div className="p-4 bg-white border-t border-gray-200 shrink-0">
        
        <div className="max-w-4xl mx-auto mb-2">
          <TagSelect selected={selectedTags} onChange={setSelectedTags} placeholder="Выбрать теги" direction="up" />
        </div>
        
        <div className="flex items-center gap-2 mb-2 px-1 max-w-4xl mx-auto">
          <button
            onClick={toggleStream}
            className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md transition-colors border ${
              useStream ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
            }`}
          >
            {useStream ? <Zap size={14} /> : <AlignLeft size={14} />}
            {useStream ? 'Стриминг ответа' : 'Полный ответ'}
          </button>
        </div>

        <div className="flex gap-3 max-w-4xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Введите сообщение..."
            disabled={loading}
            leftIcon={<MessageSquare size={18} />}
            className="flex-1 shadow-sm"
          />
          <Button 
            onClick={handleSend} 
            disabled={loading || !input.trim()} 
            className={`px-6 transition-all ${!input.trim() ? 'opacity-50 cursor-not-allowed' : 'shadow-md'}`}
          >
            <Send size={18} className={loading ? 'animate-pulse' : ''} />
          </Button>
        </div>
      </div>
    </div>
  );
}