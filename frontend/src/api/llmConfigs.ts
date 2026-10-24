import { request } from './http';

export const llmConfigsApi = {
  getLlmConfigs: () => request('/llm-configs/get'),

  updateLlmConfig: (key: string, value: string) =>
    request('/llm-configs/update', {
      method: 'PATCH',
      body: JSON.stringify({ key, value }),
    }),
};