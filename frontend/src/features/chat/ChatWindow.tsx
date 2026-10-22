import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send } from 'lucide-react';
import { Input } from '../../ui/Input';
import { Button } from '../../ui/Button';

interface ChatWindowProps {
  messages: any[];
  onSendMessage: (text: string) => Promise<void>;
  loading: boolean;
}

function cleanMarkdown(text: string): string {
  if (!text) return '';
  
  let cleaned = text;
  
  cleaned = cleaned.replace(/```(?:markdown|md)?\s*\n?/gi, '');
  cleaned = cleaned.replace(/```/g, '');
  
  cleaned = cleaned.replace(/([^\n])\n(\|.*\|)/g, '$1\n\n$2');
  
  return cleaned.trim();
}

export function ChatWindow({ messages, onSendMessage, loading }: ChatWindowProps) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    setInput('');
    await onSendMessage(text);
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => {
          const isUser = msg.chat_role === 'user';
          return (
            <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] p-4 rounded-2xl ${
                isUser 
                  ? 'bg-blue-600 text-white rounded-br-none' 
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
              }`}>
                {isUser ? (
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                ) : (
                  <div className="prose prose-sm max-w-none 
                                  prose-table:border prose-table:border-gray-300 
                                  prose-th:bg-gray-100 prose-th:px-3 prose-th:py-2 prose-th:text-left
                                  prose-td:px-3 prose-td:py-2 prose-td:border-t prose-td:border-gray-200
                                  prose-pre:bg-gray-800 prose-pre:text-gray-100">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {cleanMarkdown(msg.text)}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 p-4 rounded-2xl rounded-bl-none text-gray-500 animate-pulse">
              ConturAI печатает...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-4 bg-white border-t border-gray-200">
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