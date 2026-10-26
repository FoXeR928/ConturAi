import { request } from './http';

export const systemApi = {
  getStats: () => request('/system/stats'),
  getBackups: () => request('/system/db/backups'),
  createBackup: () => request('/system/db/backup', { method: 'POST' }),
  deleteBackup: (filename: string) => request(`/system/db/backups/${filename}`, { method: 'DELETE' }),
import { request } from './http';

export const systemApi = {
  getStats: () => request('/system/stats'),
};