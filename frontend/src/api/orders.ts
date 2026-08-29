import { apiFetch } from './client';
import type { OrderDetailResponse, OrderResponse } from '../types';

export const ordersApi = {
  listByCustomer: (customerId: string) => apiFetch<OrderDetailResponse[]>(`/customers/${customerId}/orders`),
  get: (id: string) => apiFetch<OrderDetailResponse>(`/orders/${id}`),
  updateStatus: (id: string, status: string) =>
    apiFetch<OrderResponse>(`/orders/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }),
};
