import { request } from './http';

export interface PluginInfo {
  id: string;
  name: string;
  version: string;
  description: string;
  icon: string;
  type: string;
  is_enabled: boolean;
}

export const pluginsApi = {
  getPlugins: () => request<{result: boolean, plugins: PluginInfo[]}>('/plugins/list'),
  togglePlugin: (pluginId: string, enabled: boolean) => 
    request(`/plugins/${pluginId}/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    }),
};