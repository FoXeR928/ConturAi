import { request } from './http';

export const systemApi = {
  getStats: () => request('/system/stats'),
};