import { request } from './http';

export const fewShotsApi = {
  getExamples: () => request('/few-shots/get'),
  
  createExample: (question: string, answer: string) => 
    request('/few-shots/create', {
      method: 'POST',
      body: JSON.stringify({ question, answer }),
    }),
    
  deleteExample: (id: string) => 
    request(`/few-shots/${id}`, { method: 'DELETE' }),
};