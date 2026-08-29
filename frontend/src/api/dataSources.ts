import { apiFetch } from './client';
import type { DataSourceResponse } from '../types';

export const dataSourcesApi = {
  list: () => apiFetch<DataSourceResponse[]>('/data-sources'),
  get: (id: string) => apiFetch<DataSourceResponse>(`/data-sources/${id}`),
  sync: (id: string) => apiFetch<DataSourceResponse>(`/data-sources/${id}/sync`, { method: 'POST' }),
  delete: (id: string) => apiFetch<void>(`/data-sources/${id}`, { method: 'DELETE' }),
};
