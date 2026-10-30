import { api } from './http';
import type { PluginSettings, PluginView } from '../types/plugin';

export interface RegisterPayload {
  manifest: Record<string, unknown>;
  endpoint_url: string;
}

export const pluginsApi = {
  list: (): Promise<PluginView[]> => api('/plugins'),

  toggle: (pluginId: string, isActive: boolean): Promise<PluginView> =>
    api(`/plugins/${pluginId}/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: isActive }),
    }),

  updateSettings: (
    pluginId: string,
    settings: PluginSettings,
  ): Promise<PluginView> =>
    api(`/plugins/${pluginId}/settings`, {
      method: 'PATCH',
      body: JSON.stringify({ settings }),
    }),

  register: (payload: RegisterPayload): Promise<PluginView> =>
    api('/plugins/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  remove: (pluginId: string): Promise<void> =>
    api(`/plugins/${pluginId}`, { method: 'DELETE' }),

  health: (
    pluginId: string,
  ): Promise<{ status: 'ok' | 'down'; latency_ms: number | null }> =>
    api(`/plugins/${pluginId}/health`),

  runAction: (
    pluginId: string,
    actionId: string,
  ): Promise<{ result: boolean; action_id: string }> =>
    api(`/plugins/${pluginId}/actions/${actionId}`, { method: 'POST' }),
};