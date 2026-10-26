import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Trash2, Download } from 'lucide-react';
import { Input } from '../../ui/Input';
import { Button } from '../../ui/Button';
import { chatsApi } from '../../api/chats';
import { cleanMarkdown } from '../../utils/markdown';
import { getToken, API_BASE } from '../../api/http';
import { useToast } from '../../components/ToastContext';

interface ChatWindowProps {
  messages: any[];
  onSendMessage: (text: string, tags: string[]) => Promise<void>;
  loading: boolean;
  chatId: string;
  onRefresh: () => void;
}

export function ChatWindow({ messages, onSendMessage, loading, chatId, onRefresh }: ChatWindowProps) {
  const [input, setInput] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [allTags, setAllTags] = useState<string[]>([]); // <-- Список всех тегов для подсказок
  const bottomRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Достаем роль пользователя
  const stored = localStorage.getItem('me');
  const isAdmin = stored ? JSON.parse(stored).isAdmin : false;

  // Загружаем доступные теги
  useEffect(() => {
    fetch(`${API_BASE}/ai/docs/tags`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
      .then(res => res.json())
      .then(data => setAllTags(data.tags || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    const tags = tagInput.split(',').map(t => t.trim()).filter(Boolean);
    
    setInput('');
    await onSendMessage(text, tags);
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
    // Если не админ — показываем заглушку (в будущем можно отправлять заявку)
    if (!isAdmin) {
      toast('Скачивание чатов доступно только администраторам. Запросите доступ.', 'error');
      return;
    }
    
    try {
      const token = getToken();
      const res = await fetch(`${API_BASE}/chats/export/${chatId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!res.ok) throw new Error('Ошибка экспорта');
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chat_${chatId}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      toast('Чат успешно экспортирован', 'success');
    } catch (e: any) {
      toast(e.message, 'error');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b bg-white flex justify-between items-center">
        <h2 className="font-bold text-lg text-gray-800">История диалога</h2>
        <Button variant="secondary" onClick={handleExport} className="flex items-center gap-2 text-sm px-3 py-1.5 h-auto">
          <Download size={16} /> Скачать
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => {
          const isUser = msg.chat_role === 'user';
          const isStreaming = loading && idx === messages.length - 1 && !isUser;

          return (
            <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'} group relative`}>
              <div className={`max-w-[85%] p-4 rounded-2xl ${
                isUser
                  ? 'bg-blue-600 text-white rounded-br-none'
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
                    onClick={() => handleDeleteMessage(msg.id)}
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
        <div ref={bottomRef} />
      </div>

      <div className="p-4 bg-white border-t border-gray-200">
        {/* Поле ввода тегов с автодополнением */}
        <div className="flex gap-2 max-w-4xl mx-auto mb-2">
          <datalist id="available-tags">
            {allTags.map(t => <option key={t} value={t} />)}
          </datalist>
          <input 
            list="available-tags"
            placeholder="Фильтр по тегам (начните вводить...)" 
            className="text-sm border rounded px-2 py-1 w-1/2"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
          />
        </div>
        <div className="flex gap-3 max-w-4xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Введите сообщение..."
            disabled={loading}
          />
          <Button onClick={handleSend} disabled={loading} className="px-6">
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
}