import { apiFetch } from './client';
import type { ChatMessage, ChatConfirmResponse } from '../types';

export const chatApi = {
  send: (message: string, activeEntityId?: string | null, activeEntityType?: string | null) =>
    apiFetch<{ messages: ChatMessage[] }>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        active_entity_id: activeEntityId ?? null,
        active_entity_type: activeEntityType ?? null,
      }),
    }),
  confirm: (token: string) =>
    apiFetch<ChatConfirmResponse>('/chat/action/confirm', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),
};
