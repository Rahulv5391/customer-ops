import { apiFetch } from './client';
import type { TicketResponse, TicketDetailResponse, TicketBoardRow, TicketEventResponse } from '../types';

export const ticketsApi = {
  list: (params?: { channel?: string; status?: string; priority?: string; assigned_agent_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.channel) q.set('channel', params.channel);
    if (params?.status) q.set('status', params.status);
    if (params?.priority) q.set('priority', params.priority);
    if (params?.assigned_agent_id) q.set('assigned_agent_id', params.assigned_agent_id);
    const qs = q.toString();
    return apiFetch<TicketResponse[]>(`/tickets${qs ? `?${qs}` : ''}`);
  },
  board: () => apiFetch<TicketBoardRow[]>('/tickets/board'),
  get: (id: string) => apiFetch<TicketDetailResponse>(`/tickets/${id}`),
  create: (data: { customer_id: string; subject: string; channel?: string; status?: string; priority?: string; assigned_agent_id?: string | null; category?: string }) =>
    apiFetch<TicketResponse>('/tickets', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: { status?: string; priority?: string; assigned_agent_id?: string | null; category?: string }) =>
    apiFetch<TicketResponse>(`/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  addEvent: (ticketId: string, data: { event_type: string; detail: string }) =>
    apiFetch<TicketEventResponse>(`/tickets/${ticketId}/events`, { method: 'POST', body: JSON.stringify(data) }),
};
