import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Chat, Message, chatsApi } from '../api/chats';
import { authApi } from '../api/auth';
import { ApiError } from '../api/http';
import { Markdown } from '../components/Markdown';
import { useToast } from '../components/ToastProvider';
import type { PipelineTraceItem } from '../types/plugin';

export function ChatPage() {
  const navigate = useNavigate();
  const { show } = useToast();
  const [chats, setChats] = useState<Chat[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [lastTrace, setLastTrace] = useState<PipelineTraceItem[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  const reloadChats = async () => setChats(await chatsApi.list());

  useEffect(() => {
    void reloadChats();
    authApi
      .me()
      .then((me) => setIsAdmin(me.role === 'admin'))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!activeChatId) {
      setMessages([]);
      setLastTrace([]);
      return;
    }
    chatsApi
      .messages(activeChatId)
      .then(setMessages)
      .catch(() => setMessages([]));
    setLastTrace([]);
  }, [activeChatId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingText]);

  const createChat = async () => {
    const title = prompt('Название чата:');
    if (!title) return;
    const chat = await chatsApi.create(title);
    await reloadChats();
    setActiveChatId(chat.id);
  };

  const removeChat = async (id: string) => {
    if (!confirm('Удалить чат?')) return;
    await chatsApi.remove(id);
    if (activeChatId === id) setActiveChatId(null);
    await reloadChats();
  };

  const send = async () => {
    if (!activeChatId || !input.trim() || busy) return;

    const content = input.trim();
    setInput('');
    setBusy(true);
    setTyping(true);
    setStreamingText('');
    setLastTrace([]);

    const optimisticUser: Message = {
      id: Date.now(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await chatsApi.sendStream(
        activeChatId,
        content,
        {
          onDelta: (delta) => setStreamingText((prev) => prev + delta),
          onDone: async (info) => {
            const finalText = await new Promise<string>((resolve) => {
              setStreamingText((prev) => {
                resolve(prev);
                return prev;
              });
            });
            setMessages((prev) => [
              ...prev,
              {
                id: info.assistant_message_id,
                role: 'assistant',
                content: finalText,
                created_at: new Date().toISOString(),
              },
            ]);
            setStreamingText('');
            setTyping(false);
            setLastTrace(info.trace);
          },
          onError: (msg) => {
            show(msg, 'error');
            setTyping(false);
            setStreamingText('');
          },
        },
        controller.signal,
      );
    } catch (err) {
      if (!(err instanceof DOMException && err.name === 'AbortError')) {
        show(
          err instanceof ApiError ? err.message : 'Ошибка отправки',
          'error',
        );
      }
      setTyping(false);
      setStreamingText('');
    } finally {
      setBusy(false);
      abortRef.current = null;
    }
  };

  const stopStream = () => {
    abortRef.current?.abort();
    setBusy(false);
    setTyping(false);
  };

  const logout = () => {
    authApi.logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-64 bg-slate-900 text-slate-100 p-4 space-y-3
                        flex flex-col">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-sm">ConturAI</span>
          <button
            onClick={logout}
            className="text-xs text-slate-400 hover:text-white"
          >
            Выйти
          </button>
        </div>
        <div className="flex flex-col gap-1">
          <button
            onClick={createChat}
            className="w-full py-2 rounded-lg bg-indigo-600 text-white
                       text-sm hover:bg-indigo-700"
          >
            + Новый чат
          </button>
          {isAdmin && (
            <button
              onClick={() => navigate('/plugins')}
              className="w-full py-2 rounded-lg bg-slate-800 text-white
                         text-sm hover:bg-slate-700"
            >
              Плагины
            </button>
          )}
          <button
            onClick={() => navigate('/profile')}
            className="w-full py-2 rounded-lg bg-slate-800 text-white
                       text-sm hover:bg-slate-700"
          >
            Профиль
          </button>
        </div>
        <div className="flex-1 overflow-y-auto space-y-1">
          {chats.map((chat) => (
            <div
              key={chat.id}
              className={
                'flex items-center justify-between px-3 py-2 rounded-lg ' +
                'text-sm cursor-pointer ' +
                (activeChatId === chat.id
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-400 hover:bg-slate-800/60')
              }
              onClick={() => setActiveChatId(chat.id)}
            >
              <span className="truncate">{chat.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  void removeChat(chat.id);
                }}
                className="text-xs text-slate-500 hover:text-rose-400"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        {!activeChatId && (
          <div className="flex-1 flex items-center justify-center
                          text-slate-400 text-sm">
            Выберите или создайте чат
          </div>
        )}
        {activeChatId && (
          <>
            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={
                    'max-w-2xl p-3 rounded-lg text-sm ' +
                    (m.role === 'user'
                      ? 'ml-auto bg-indigo-600 text-white'
                      : 'bg-white border border-slate-200 text-slate-800')
                  }
                >
                  {m.role === 'assistant' ? (
                    <Markdown>{m.content}</Markdown>
                  ) : (
                    <span className="whitespace-pre-wrap">{m.content}</span>
                  )}
                </div>
              ))}
              {typing && (
                <div className="max-w-2xl p-3 rounded-lg bg-white border
                                border-slate-200 text-slate-800 text-sm">
                  {streamingText ? (
                    <Markdown>{streamingText}</Markdown>
                  ) : (
                    <span className="text-slate-400 animate-pulse">
                      Обработка пайплайна...
                    </span>
                  )}
                </div>
              )}
              {messages.length === 0 && !typing && (
                <p className="text-center text-sm text-slate-400">
                  Начните диалог — запрос пройдёт через все активные плагины.
                </p>
              )}
              {lastTrace.length > 0 && !typing && (
                <details className="text-xs text-slate-400 mt-2">
                  <summary className="cursor-pointer hover:text-slate-600">
                    Пайплайн: {lastTrace.length} шаг(ов)
                  </summary>
                  <ul className="mt-2 space-y-0.5 pl-4">
                    {lastTrace.map((t, i) => (
                      <li key={i}>
                        <span
                          className={
                            t.ok ? 'text-emerald-600' : 'text-rose-600'
                          }
                        >
                          {t.ok ? '✓' : '✗'}
                        </span>{' '}
                        {t.plugin_name}{' '}
                        <span className="text-slate-400">
                          ({t.duration_ms} ms)
                        </span>
                        {t.error && (
                          <span className="text-rose-500 ml-1">
                            — {t.error}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              <div ref={bottomRef} />
            </div>
            <div className="p-4 bg-white border-t border-slate-200
                            space-y-2">
              <div className="flex gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      void send();
                    }
                  }}
                  placeholder="Сообщение..."
                  disabled={busy}
                  className="flex-1 px-3 py-2 rounded-lg border
                             border-slate-300 text-sm
                             focus:outline-none focus:ring-2
                             focus:ring-indigo-500"
                />
                {typing ? (
                  <button
                    onClick={stopStream}
                    className="px-4 py-2 rounded-lg bg-rose-600 text-white
                               text-sm font-medium hover:bg-rose-700"
                  >
                    Стоп
                  </button>
                ) : (
                  <button
                    onClick={() => void send()}
                    disabled={busy || !input.trim()}
                    className="px-4 py-2 rounded-lg bg-indigo-600 text-white
                               text-sm hover:bg-indigo-700
                               disabled:opacity-60"
                  >
                    →
                  </button>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}