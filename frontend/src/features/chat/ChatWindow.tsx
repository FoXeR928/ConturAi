import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send } from 'lucide-react';
import { Input } from '../../ui/Input';
import { Button } from '../../ui/Button';

interface ChatWindowProps {
  messages: any[];
  onSendMessage: (text: string) => Promise<void>;
  loading: boolean;
}

export function ChatWindow({ messages, onSendMessage, loading }: ChatWindowProps) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  // Автоскролл вниз при новом сообщении
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
      {/* Область сообщений */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg, idx) => {
          const isUser = msg.chat_role === 'user' || msg.role === 'user';
          return (
            <div key={idx} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] p-4 rounded-2xl ${
                isUser 
                  ? 'bg-blue-600 text-white rounded-br-none' 
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
              }`}>
                <ReactMarkdown className="prose prose-sm max-w-none">
                  {msg.text}
                </ReactMarkdown>
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

      {/* Поле ввода */}
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