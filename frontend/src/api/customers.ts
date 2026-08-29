import { apiFetch } from './client';
import type { CustomerResponse, CustomerDetailResponse, NoteResponse } from '../types';

export const customersApi = {
  list: (params?: { query?: string; status?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.query) q.set('query', params.query);
    if (params?.status) q.set('status', params.status);
    if (params?.limit != null) q.set('limit', String(params.limit));
    if (params?.offset != null) q.set('offset', String(params.offset));
    const qs = q.toString();
    return apiFetch<CustomerResponse[]>(`/customers${qs ? `?${qs}` : ''}`);
  },
  get: (id: string) => apiFetch<CustomerDetailResponse>(`/customers/${id}`),
  create: (data: Partial<CustomerResponse>) =>
    apiFetch<CustomerResponse>('/customers', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<CustomerResponse>) =>
    apiFetch<CustomerResponse>(`/customers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  addNote: (customerId: string, body: string) =>
    apiFetch<NoteResponse>(`/customers/${customerId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ body }),
    }),
};
