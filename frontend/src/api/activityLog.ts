import { apiFetch } from './client';
import type { ActivityLogResponse } from '../types';

export const activityLogApi = {
  list: (params?: { entity_type?: string; entity_id?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.entity_type) q.set('entity_type', params.entity_type);
    if (params?.entity_id) q.set('entity_id', params.entity_id);
    if (params?.limit != null) q.set('limit', String(params.limit));
    if (params?.offset != null) q.set('offset', String(params.offset));
    const qs = q.toString();
    return apiFetch<ActivityLogResponse[]>(`/activity-log${qs ? `?${qs}` : ''}`);
  },
};
