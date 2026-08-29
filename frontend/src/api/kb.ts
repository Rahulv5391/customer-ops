import { apiFetch, apiFetchForm } from './client';
import type { KBDocumentResponse, KBSearchHit } from '../types';

export const kbApi = {
  list: (category?: string) => {
    const q = category ? `?category=${category}` : '';
    return apiFetch<KBDocumentResponse[]>(`/kb${q}`);
  },
  get: (id: string) => apiFetch<KBDocumentResponse>(`/kb/${id}`),
  upload: (formData: FormData) => apiFetchForm<KBDocumentResponse>('/kb/upload', formData),
  updateMeta: (id: string, data: { title?: string; category?: string; version?: string; source_updated_at?: string }) =>
    apiFetch<KBDocumentResponse>(`/kb/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  replaceContent: (id: string, formData: FormData) => apiFetchForm<KBDocumentResponse>(`/kb/${id}/upload`, formData, 'PATCH'),
  delete: (id: string) => apiFetch<void>(`/kb/${id}`, { method: 'DELETE' }),
  search: (query: string) =>
    apiFetch<KBSearchHit[]>('/kb/search', { method: 'POST', body: JSON.stringify({ query }) }),
};
