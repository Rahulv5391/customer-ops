import { apiFetch } from './client';
import type { DataSourceResponse } from '../types';

export const dataSourcesApi = {
  list: () => apiFetch<DataSourceResponse[]>('/data-sources'),
  get: (id: string) => apiFetch<DataSourceResponse>(`/data-sources/${id}`),
  create: (data: { name: string; connector_type: string }) =>
    apiFetch<DataSourceResponse>('/data-sources', { method: 'POST', body: JSON.stringify(data) }),
  sync: (id: string) => apiFetch<DataSourceResponse>(`/data-sources/${id}/sync`, { method: 'POST' }),
  delete: (id: string) => apiFetch<void>(`/data-sources/${id}`, { method: 'DELETE' }),
};
