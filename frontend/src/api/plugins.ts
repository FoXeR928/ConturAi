import { request } from './http';

export interface PluginItem {
  id: string;
  name: string;
  // URL на JS-файл плагина для фронтенда
  frontend_chat_button?: string;
  frontend_admin_tab?: { label: string; component_url: string };
}

export const pluginsApi = {
  getActivePlugins: () => request<{ plugins: PluginItem[] }>('/plugins/active'),
  togglePlugin: (id: string) => request(`/plugins/toggle?id=${id}`, { method: 'PATCH' }),
};