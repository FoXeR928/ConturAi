import { api } from './http';
import type { PluginSettings, PluginView } from '../types/plugin';

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
};