import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Trash2, Download, Zap, AlignLeft, ChevronDown, Check, X } from 'lucide-react';
import { Input } from '../../ui/Input';
import { Button } from '../../ui/Button';
import { chatsApi } from '../../api/chats';
import { cleanMarkdown } from '../../utils/markdown';
import { useToast } from '../../components/ToastContext';
import { tagsApi, TagItem } from '../../api/tags';

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
}

// ==============================================================================
// БЛОК 2: КОМПОНЕНТ И СОСТОЯНИЯ
// ==============================================================================

export function ChatWindow({ messages, onSendMessage, loading, chatId, onRefresh }: ChatWindowProps) {
  const [input, setInput] = useState('');
  
  // Состояния для тегов
  const [allTags, setAllTags] = useState<TagItem[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Состояние переключателя стриминга
  const [useStream, setUseStream] = useState<boolean>(() => {
    const saved = localStorage.getItem('use_stream');
    return saved !== null ? saved === 'true' : false;
  });

  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  // ==========================================================================
  // БЛОК 3: ЭФФЕКТЫ (ЗАГРУЗКА ТЕГОВ, КЛИК ВНЕ, АВТОСКРОЛЛ)
  // ==========================================================================

  // Загрузка доступных тегов
  useEffect(() => {
    tagsApi.getTags()
      .then(data => setAllTags(data.tags || []))
      .catch(() => {});
  }, []);

  // Закрытие выпадающего списка по клику вне его области
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Умный автоскролл (не дергает экран, если пользователь читает историю выше)
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (container) {
      // Проверяем, находится ли пользователь в самом низу (погрешность 100px)
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
      if (isNearBottom) {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [messages]);

  // ==========================================================================
  // БЛОК 4: ДЕЙСТВИЯ
  // ==========================================================================

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    
    setInput(''); // Мгновенно очищаем поле ввода
    
    // После отправки прокручиваем вниз
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    
    await onSendMessage(text, selectedTags, useStream);
  };

  const toggleTag = (tagName: string) => {
    setSelectedTags(prev => 
      prev.includes(tagName) ? prev.filter(t => t !== tagName) : [...prev, tagName]
    );
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
    if (!isAdmin) {
      toast('Скачивание чатов доступно только администраторам.', 'error');
      return;
    }
    
    try {
      await chatsApi.exportChat(chatId, `chat_${chatId}.md`);
      toast('Чат успешно экспортирован', 'success');
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  // ==========================================================================
  // БЛОК 5: РЕНДЕР ИНТЕРФЕЙСА
  // ==========================================================================

  return (
    <div className="flex flex-col h-full bg-gray-50/50">
      
      {/* Шапка чата */}
      <div className="p-4 border-b bg-white flex justify-between items-center shrink-0">
        <h2 className="font-bold text-lg text-gray-800">История диалога</h2>
        <Button variant="secondary" onClick={handleExport} className="flex items-center gap-2 text-sm px-3 py-1.5 h-auto">
          <Download size={16} /> Скачать
        </Button>
      </div>

      {/* Лента сообщений */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6" ref={scrollContainerRef}>
        {messages.map((msg, idx) => {
          const isUser = msg.chat_role === 'user';
          // Проверяем, является ли это последнее сообщение, и идет ли сейчас стриминг
          const isStreaming = loading && idx === messages.length - 1 && !isUser;

          return (
            <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'} group relative`}>
              <div className={`max-w-[85%] p-4 rounded-2xl ${
                isUser
                  ? 'bg-blue-600 text-white rounded-br-none shadow-md shadow-blue-200'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
              }`}>
                
                {/* Рендер текста сообщения */}
                {isUser ? (
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                ) : (
                  <div className="prose prose-sm max-w-none prose-table:border prose-table:border-gray-300 prose-th:bg-gray-100 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-td:px-3 prose-td:py-2 prose-td:border-t prose-td:border-gray-200 prose-pre:bg-gray-800 prose-pre:text-gray-100">
                    {msg.text ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {cleanMarkdown(msg.text)}
                      </ReactMarkdown>
                    ) : (
                      // Курсор, если идет стриминг и текст еще пуст
                      isStreaming && <span className="animate-pulse">▍</span>
                    )}
                  </div>
                )}

                {/* Кнопка удаления (появляется при наведении) */}
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

      {/* Панель ввода (прибита к низу) */}
      <div className="p-4 bg-white border-t border-gray-200 shrink-0">
        
        {/* Выбор тегов */}
        <div className="flex flex-wrap items-center gap-2 max-w-4xl mx-auto mb-2" ref={dropdownRef}>
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-2 text-sm border border-gray-300 rounded-lg px-3 py-1.5 bg-white hover:bg-gray-50 text-gray-700 min-w-[180px] justify-between transition-colors focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <span>Выбрать теги {selectedTags.length > 0 && `(${selectedTags.length})`}</span>
              <ChevronDown size={16} className={`transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Выпадающее меню */}
            {isDropdownOpen && (
              <div className="absolute bottom-full left-0 mb-2 w-64 bg-white border rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto">
                {allTags.length === 0 ? (
                  <div className="p-3 text-gray-500 text-sm text-center">Нет доступных тегов</div>
                ) : (
                  allTags.map(tag => (
                    <div 
                      key={tag.id}
                      onClick={() => toggleTag(tag.name)}
                      className="flex items-center justify-between px-3 py-2.5 hover:bg-gray-50 cursor-pointer text-sm border-b last:border-0"
                    >
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: tag.color }} />
                        <span className="font-medium text-gray-700">{tag.name}</span>
                      </div>
                      {selectedTags.includes(tag.name) && <Check size={16} className="text-blue-600" />}
                    </div>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Выбранные теги (чипсы) */}
          {selectedTags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {selectedTags.map(t => {
                const tagInfo = allTags.find(tag => tag.name === t);
                return (
                  <span 
                    key={t} 
                    className="text-xs px-2.5 py-1 rounded-full text-white flex items-center gap-1 shadow-sm font-medium"
                    style={{ backgroundColor: tagInfo?.color || '#3b82f6' }}
                  >
                    {t}
                    <button onClick={() => toggleTag(t)} className="hover:bg-black/20 rounded-full p-0.5 ml-0.5">
                      <X size={12} />
                    </button>
                  </span>
                );
              })}
            </div>
          )}
        </div>
        
        {/* Переключатель стриминга */}
        <div className="flex items-center gap-2 mb-2 px-1 max-w-4xl mx-auto">
          <button
            onClick={toggleStream}
            className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md transition-colors border ${
              useStream 
                ? 'bg-blue-50 text-blue-700 border-blue-200' 
                : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
            }`}
            title="Если включено, ответ будет появляться по мере генерации"
          >
            {useStream ? <Zap size={14} /> : <AlignLeft size={14} />}
            {useStream ? 'Стриминг ответа' : 'Полный ответ'}
          </button>
          <span className="text-[11px] text-gray-400">
            {useStream ? 'Текст появляется по мере генерации' : 'Ожидание полного ответа'}
          </span>
        </div>

        {/* Поле ввода и кнопка отправки */}
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