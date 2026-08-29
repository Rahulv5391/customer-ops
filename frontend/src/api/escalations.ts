import { apiFetch } from './client';
import type { EscalationResponse } from '../types';

export const escalationsApi = {
  list: (params?: { status?: string; priority?: string; escalation_type?: string; ticket_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.priority) q.set('priority', params.priority);
    if (params?.escalation_type) q.set('escalation_type', params.escalation_type);
    if (params?.ticket_id) q.set('ticket_id', params.ticket_id);
    const qs = q.toString();
    return apiFetch<EscalationResponse[]>(`/escalations${qs ? `?${qs}` : ''}`);
  },
  get: (id: string) => apiFetch<EscalationResponse>(`/escalations/${id}`),
  resolve: (id: string, data: { status: 'approved' | 'rejected'; rejection_note?: string }) =>
    apiFetch<EscalationResponse>(`/escalations/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
};
