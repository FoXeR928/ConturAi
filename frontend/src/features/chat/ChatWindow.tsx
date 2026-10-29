import { useState, useEffect, useRef } from 'react';
import { chatsApi, Message } from '../../api/chats';
import { Input } from '../../ui/Input';
import { Button } from '../../ui/Button';
import { Send } from 'lucide-react';

export function ChatWindow({ chatId }: { chatId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = async () => {
    const data = await chatsApi.getMessages(chatId);
    setMessages(data.messages_history || []);
  };

  useEffect(() => { load(); }, [chatId]);
  
  useEffect(() => { 
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const text = input;
    setInput('');
    
    // Оптимистичное обновление (сразу показываем сообщение)
    setMessages(prev => [...prev, { 
      id: Date.now().toString(), 
      chat_role: 'user', 
      text, 
      created_at: new Date().toISOString() 
    }]);
    
    try {
      await chatsApi.createMessage(chatId, text);
      load(); // Перезагружаем историю, чтобы получить реальные ID из БД
    } catch (err) {
      console.error("Ошибка отправки", err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50/50">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => {
          const isUser = msg.chat_role === 'user';
          return (
            <div key={msg.id || i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-4 rounded-2xl ${
                isUser ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white border text-gray-800 rounded-bl-none'
              }`}>
                {msg.text}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
      
      <div className="p-4 bg-white border-t">
        <div className="flex gap-3 max-w-4xl mx-auto">
          <Input 
            value={input} 
            onChange={e => setInput(e.target.value)} 
            onKeyDown={e => e.key === 'Enter' && handleSend()} 
            placeholder="Введите сообщение..." 
          />
          <Button onClick={handleSend}><Send size={18} /></Button>
        </div>
      </div>
    </div>
  );
}