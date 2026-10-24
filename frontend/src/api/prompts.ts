import { request } from './http';

export const promptsApi = {
  getPrompts: () => request('/prompts/get'),

  updatePrompt: (key: string, value: string) =>
    request('/prompts/update', {
      method: 'PATCH',
      body: JSON.stringify({ key, value }),
    }),
};