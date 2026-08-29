import { apiFetch } from './client';
import type { AgentResponse } from '../types';

export const agentsApi = {
  list: (params?: { team?: string; on_duty?: boolean }) => {
    const q = new URLSearchParams();
    if (params?.team) q.set('team', params.team);
    if (params?.on_duty != null) q.set('on_duty', String(params.on_duty));
    const qs = q.toString();
    return apiFetch<AgentResponse[]>(`/agents${qs ? `?${qs}` : ''}`);
  },
  get: (id: string) => apiFetch<AgentResponse>(`/agents/${id}`),
  create: (data: { full_name: string; email: string; password: string; role?: string; team?: string; shift_start?: string; shift_end?: string; on_duty?: boolean }) =>
    apiFetch<AgentResponse>('/agents', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<AgentResponse & { password?: string }>) =>
    apiFetch<AgentResponse>(`/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: (id: string) => apiFetch<AgentResponse>(`/agents/${id}`, { method: 'DELETE' }),
};
