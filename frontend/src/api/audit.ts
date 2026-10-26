import { request } from './http';

export const auditApi = {
  getLogs: (limit = 50, offset = 0) => 
    request(`/audit/list?limit=${limit}&offset=${offset}`),
};