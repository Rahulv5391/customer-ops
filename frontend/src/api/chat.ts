import { apiFetch } from './client';
import type { ChatMessage, ChatConfirmResponse } from '../types';

export const chatApi = {
  send: (message: string, sessionId: string) =>
    apiFetch<{ messages: ChatMessage[] }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),
  confirm: (token: string) =>
    apiFetch<ChatConfirmResponse>('/chat/action/confirm', {
      method: 'POST',
      body: JSON.stringify({ token }),
    }),
};
