import { apiFetch } from './client';
import type { LoginResponse, AgentResponse } from '../types';

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => apiFetch<AgentResponse>('/auth/me'),
};
