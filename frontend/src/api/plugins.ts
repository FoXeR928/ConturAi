import { api } from './http';
import type { PluginSettings, PluginView } from '../types/plugin';

export interface RegisterPayload {
  manifest: Record<string, unknown>;
  endpoint_url: string;
}

export interface HealthCheck {
  status: 'ok' | 'down';
  latency_ms: number | null;
}

export interface ActionResponse {
  result: boolean;
  action_id: string;
}

export const pluginsApi = {
  list: (): Promise<PluginView[]> => api<PluginView[]>('/plugins'),

  toggle: (pluginId: string, isActive: boolean): Promise<PluginView> =>
    api<PluginView>(`/plugins/${pluginId}/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive }),
    }),

  updateSettings: (
    pluginId: string,
    settings: PluginSettings,
  ): Promise<PluginView> =>
    api<PluginView>(`/plugins/${pluginId}/settings`, {
      method: 'PATCH',
      body: JSON.stringify({ settings }),
    }),

  register: (payload: RegisterPayload): Promise<PluginView> =>
    api<PluginView>('/plugins/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  remove: (pluginId: string): Promise<void> =>
    api<void>(`/plugins/${pluginId}`, { method: 'DELETE' }),

  health: (pluginId: string): Promise<HealthCheck> =>
    api<HealthCheck>(`/plugins/${pluginId}/health`),

  runAction: (
    pluginId: string,
    actionId: string,
  ): Promise<ActionResponse> =>
    api<ActionResponse>(`/plugins/${pluginId}/actions/${actionId}`, {
      method: 'POST',
    }),
};