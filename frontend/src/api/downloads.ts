import { request } from './http';

export const downloadsApi = {
  requestAccess: (uploadId: string) => request('/downloads/request', {
    method: 'POST',
    body: JSON.stringify({ upload_id: uploadId }),
  }),
  
  listRequests: () => request('/downloads/list'),
  
  processRequest: (requestId: string, action: 'approve' | 'reject') => request('/downloads/action', {
    method: 'POST',
    body: JSON.stringify({ request_id: requestId, action }),
  }),
};