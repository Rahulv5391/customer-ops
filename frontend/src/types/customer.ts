export type AccountTier = 'free' | 'pro' | 'enterprise';
export type CustomerStatus = 'active' | 'inactive' | 'at_risk';
export type OrderStatus = 'placed' | 'shipped' | 'delivered' | 'refunded' | 'cancelled';

export interface CustomerResponse {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  company: string | null;
  account_tier: AccountTier;
  status: CustomerStatus;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  region: string | null;
  postal_code: string | null;
  country: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  sku: string;
  product_name: string;
  quantity: number;
  unit_price: string;
}

export interface OrderResponse {
  id: string;
  customer_id: string;
  order_number: string;
  status: OrderStatus;
  total_amount: string;
  currency: string;
  placed_at: string;
  updated_at: string;
}

export interface OrderDetailResponse extends OrderResponse {
  items: OrderItem[];
}

export interface NoteResponse {
  id: string;
  customer_id: string;
  author: string;
  body: string;
  created_at: string;
}

export interface CustomerDetailResponse extends CustomerResponse {
  orders: OrderDetailResponse[];
  tickets: import('./ticket').TicketDetailResponse[];
  notes: NoteResponse[];
}
