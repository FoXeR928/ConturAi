export interface ChatRoom {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  room_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface PluginInfo {
  id: string;
  name: string;
  version: string;
  type: "local" | "remote";
  status: "inactive" | "active" | "error";
  error: string | null;
  has_settings: boolean;
  endpoint_url: string | null;
  is_inference_provider: boolean;
}

export interface PluginConfigResponse {
  plugin_id: string;
  schema: JsonSchema;
  current: Record<string, unknown>;
}

export interface JsonSchema {
  title?: string;
  description?: string;
  type?: string;
  properties?: Record<string, JsonSchemaProperty>;
  required?: string[];
  $defs?: Record<string, JsonSchema>;
}

export interface JsonSchemaProperty {
  title?: string;
  description?: string;
  type?: string | string[];
  default?: unknown;
  enum?: unknown[];
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
  exclusiveMaximum?: number;
  items?: JsonSchemaProperty;
  anyOf?: JsonSchemaProperty[];
  $ref?: string;
}

function authHeaders(token?: string | null): HeadersInit {
  const h: HeadersInit = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function request<T>(
  url: string,
  init: RequestInit = {},
  token?: string | null
): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: {
      ...authHeaders(token),
      ...(init.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {}
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  auth: {
    login: async (username: string, password: string) => {
      const body = new URLSearchParams({ username, password });
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      if (!res.ok) {
        let detail = "Ошибка входа";
        try {
          const data = await res.json();
          if (data?.detail) detail = data.detail;
        } catch {}
        throw new Error(detail);
      }
      return (await res.json()) as { access_token: string; token_type: string };
    },
    me: (token: string) =>
      request<{ id: string; username: string; role: "admin" | "user"; created_at: string }>(
        "/api/auth/me",
        {},
        token
      ),
  },

  chats: {
    list: (token: string) => request<ChatRoom[]>("/api/chats", {}, token),
    create: (token: string, title?: string) =>
      request<ChatRoom>(
        "/api/chats",
        { method: "POST", body: JSON.stringify({ title: title ?? null }) },
        token
      ),
    remove: (token: string, id: string) =>
      request<void>(`/api/chats/${id}`, { method: "DELETE" }, token),
    messages: (token: string, id: string) =>
      request<Message[]>(`/api/chats/${id}/messages`, {}, token),
  },

  admin: {
    plugins: (token: string) =>
      request<PluginInfo[]>("/api/admin/plugins", {}, token),
    toggle: (token: string, id: string, active: boolean) =>
      request<PluginInfo>(
        `/api/admin/plugins/${id}/toggle`,
        { method: "POST", body: JSON.stringify({ active }) },
        token
      ),
    getConfig: (token: string, id: string) =>
      request<PluginConfigResponse>(
        `/api/admin/plugins/${id}/config`,
        {},
        token
      ),
    saveConfig: (token: string, id: string, settings: Record<string, unknown>) =>
      request<PluginConfigResponse>(
        `/api/admin/plugins/${id}/config`,
        { method: "POST", body: JSON.stringify({ settings }) },
        token
      ),
  },
};

// ---- SSE Streaming (POST) -------------------------------------------------

export interface StreamHandlers {
  onToken: (token: string) => void;
  onDone: (payload: { message_id: string | null; length: number }) => void;
  onError: (error: Error) => void;
}

export async function streamMessage(
  token: string,
  roomId: string,
  content: string,
  handlers: StreamHandlers,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`/api/chats/${roomId}/messages/stream`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ content }),
    signal,
  });

  if (!res.ok || !res.body) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) msg = data.detail;
    } catch {}
    throw new Error(msg);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let idx: number;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const chunk = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);

        let event = "message";
        let data = "";
        for (const line of chunk.split("\n")) {
          if (line.startsWith("event:")) event = line.slice(6).trim();
          else if (line.startsWith("data:")) data += line.slice(5).trim();
        }
        if (!data) continue;
        let parsed: any;
        try {
          parsed = JSON.parse(data);
        } catch {
          continue;
        }
        if (event === "token") handlers.onToken(parsed.token ?? "");
        else if (event === "done") handlers.onDone(parsed);
        else if (event === "error")
          handlers.onError(new Error(parsed.error || "stream error"));
      }
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {}
  }
}