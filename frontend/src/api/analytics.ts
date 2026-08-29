import { apiFetch } from './client';
import type { AnalyticsSummary, TicketVolumePoint, TopIssueCategory } from '../types';

export const analyticsApi = {
  summary: () => apiFetch<AnalyticsSummary>('/analytics/summary'),
  ticketVolume: (days = 7) => apiFetch<TicketVolumePoint[]>(`/analytics/ticket-volume?days=${days}`),
  topIssueCategories: (limit = 5) => apiFetch<TopIssueCategory[]>(`/analytics/top-issue-categories?limit=${limit}`),
  escalationsPending: () => apiFetch<{ count: number }>('/analytics/escalations-pending'),
  ticketsResolvedToday: () => apiFetch<{ count: number }>('/analytics/tickets-resolved-today'),
};
