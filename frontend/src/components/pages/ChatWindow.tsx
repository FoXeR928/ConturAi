import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import {
  api,
  ChatRoom,
  Message,
  streamMessage,
} from "../services/api";
import { Button, Input } from "../components/shared/DesignSystem";
import { UIExtensionSlot } from "../context/SlotEngine";

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ChatWindow() {
  const { token } = useAuth();
  const { push } = useToast();

  const [rooms, setRooms] = useState<ChatRoom[]>([]);
  const [activeRoomId, setActiveRoomId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [streamingText, setStreamingText] = useState<string>("");
  const [creating, setCreating] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // ---- Загрузка комнат ----------------------------------------------------

  const loadRooms = useCallback(async () => {
    if (!token) return;
    try {
      const list = await api.chats.list(token);
      setRooms(list);
      if (!activeRoomId && list.length > 0) {
        setActiveRoomId(list[0].id);
      }
    } catch (err) {
      push((err as Error).message, "error");
    }
  }, [token, activeRoomId, push]);

  useEffect(() => {
    loadRooms();
  }, [loadRooms]);

  // ---- Загрузка сообщений -------------------------------------------------

  useEffect(() => {
    if (!token || !activeRoomId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    api.chats
      .messages(token, activeRoomId)
      .then((m) => {
        if (!cancelled) setMessages(m);
      })
      .catch((err) => push((err as Error).message, "error"));
    return () => {
      cancelled = true;
    };
  }, [token, activeRoomId, push]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, scrollToBottom]);

  // ---- Создание комнаты ---------------------------------------------------

  const createRoom = async () => {
    if (!token || creating) return;
    setCreating(true);
    try {
      const room = await api.chats.create(token);
      setRooms((prev) => [room, ...prev]);
      setActiveRoomId(room.id);
      setMessages([]);
    } catch (err) {
      push((err as Error).message, "error");
    } finally {
      setCreating(false);
    }
  };

  const deleteRoom = async (id: string) => {
    if (!token) return;
    if (!confirm("Удалить чат?")) return;
    try {
      await api.chats.remove(token, id);
      setRooms((prev) => prev.filter((r) => r.id !== id));
      if (activeRoomId === id) {
        setActiveRoomId(rooms.find((r) => r.id !== id)?.id ?? null);
      }
    } catch (err) {
      push((err as Error).message, "error");
    }
  };

  // ---- Отправка сообщения (SSE) -------------------------------------------

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !activeRoomId || !input.trim() || sending) return;

    const content = input.trim();
    setInput("");
    setSending(true);
    setStreamingText("");

    // Локально добавляем сообщение пользователя
    const optimisticUser: Message = {
      id: `local-${Date.now()}`,
      room_id: activeRoomId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    const controller = new AbortController();
    abortRef.current = controller;

    let buffer = "";
    try {
      await streamMessage(
        token,
        activeRoomId,
        content,
        {
          onToken: (tok) => {
            buffer += tok;
            setStreamingText(buffer);
          },
          onDone: () => {
            const assistant: Message = {
              id: `local-assistant-${Date.now()}`,
              room_id: activeRoomId,
              role: "assistant",
              content: buffer,
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistant]);
            setStreamingText("");
            buffer = "";
          },
          onError: (err) => {
            push(err.message, "error");
            if (buffer) {
              setMessages((prev) => [
                ...prev,
                {
                  id: `local-assistant-${Date.now()}`,
                  room_id: activeRoomId,
                  role: "assistant",
                  content: buffer,
                  created_at: new Date().toISOString(),
                },
              ]);
            }
            setStreamingText("");
            buffer = "";
          },
        },
        controller.signal
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        push((err as Error).message, "error");
      }
    } finally {
      setSending(false);
      abortRef.current = null;
    }
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
  };

  const activeRoom = rooms.find((r) => r.id === activeRoomId);

  // ---- UI -----------------------------------------------------------------

  return (
    <div className="flex-1 flex min-h-0">
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-800 flex flex-col bg-slate-950/60">
        <div className="p-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            Чаты
          </span>
          <Button size="sm" variant="secondary" onClick={createRoom} loading={creating}>
            + Новый
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {rooms.length === 0 && (
            <div className="text-xs text-slate-500 text-center py-8">
              Нет чатов. Создайте первый.
            </div>
          )}
          {rooms.map((r) => {
            const isActive = r.id === activeRoomId;
            return (
              <div
                key={r.id}
                className={`group flex items-center justify-between gap-1 rounded-lg px-2.5 py-2 cursor-pointer transition ${
                  isActive
                    ? "bg-brand-600/15 border border-brand-600/30"
                    : "hover:bg-slate-800/60 border border-transparent"
                }`}
                onClick={() => setActiveRoomId(r.id)}
              >
                <span
                  className={`text-sm truncate ${
                    isActive ? "text-brand-200" : "text-slate-300"
                  }`}
                >
                  {r.title || "Без названия"}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteRoom(r.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 text-xs transition"
                  title="Удалить"
                >
                  ✕
                </button>
              </div>
            );
          })}
        </div>

        {/* Слот: chat.sidebar.bottom */}
        <div className="border-t border-slate-800 p-3">
          <UIExtensionSlot name="chat.sidebar.bottom" />
        </div>
      </aside>

      {/* Main */}
      <section className="flex-1 flex flex-col min-w-0">
        {activeRoom ? (
          <>
            {/* Header */}
            <div className="border-b border-slate-800 px-6 py-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-200 truncate">
                {activeRoom.title || "Без названия"}
              </h2>
              <UIExtensionSlot name="chat.header.right" />
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
              <div className="max-w-3xl mx-auto space-y-4">
                {messages.length === 0 && !streamingText && (
                  <div className="text-center text-sm text-slate-500 py-16">
                    Начните диалог — отправьте первое сообщение.
                  </div>
                )}

                {messages.map((m) => (
                  <MessageBubble key={m.id} message={m} />
                ))}

                {streamingText && (
                  <MessageBubble
                    message={{
                      id: "stream",
                      room_id: activeRoomId!,
                      role: "assistant",
                      content: streamingText,
                      created_at: new Date().toISOString(),
                    }}
                    streaming
                  />
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input */}
            <div className="border-t border-slate-800 px-6 py-4">
              <form
                onSubmit={sendMessage}
                className="max-w-3xl mx-auto flex items-end gap-2"
              >
                <div className="flex-1">
                  <div className="relative">
                    <Input
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Напишите сообщение…"
                      disabled={sending}
                      className="pr-12 py-3"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                      {/* Слот: chat.input.actions */}
                      <UIExtensionSlot name="chat.input.actions" />
                    </div>
                  </div>
                </div>
                {sending ? (
                  <Button
                    type="button"
                    variant="danger"
                    onClick={stopStreaming}
                    size="md"
                  >
                    Стоп
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    disabled={!input.trim()}
                    size="md"
                  >
                    Отправить
                  </Button>
                )}
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-sm text-slate-500">
            Выберите или создайте чат
          </div>
        )}
      </section>
    </div>
  );
}

function MessageBubble({
  message,
  streaming = false,
}: {
  message: Message;
  streaming?: boolean;
}) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-semibold ${
          isUser
            ? "bg-slate-700 text-slate-200"
            : "bg-gradient-to-br from-brand-500 to-purple-600 text-white"
        }`}
      >
        {isUser ? "Я" : "AI"}
      </div>
      <div className={`flex-1 max-w-[80%] ${isUser ? "text-right" : ""}`}>
        <div
          className={`inline-block text-left px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap break-words ${
            isUser
              ? "bg-brand-600 text-white"
              : "bg-slate-800 text-slate-100 border border-slate-700"
          }`}
        >
          {message.content}
          {streaming && (
            <span className="inline-block w-1.5 h-4 bg-brand-400 ml-1 align-middle animate-pulse" />
          )}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  );
}