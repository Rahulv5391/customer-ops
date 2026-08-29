export type TicketStatus = 'unassigned' | 'in_progress' | 'pending_qa' | 'resolved' | 'closed';
export type TicketChannel = 'email' | 'chat' | 'phone' | 'social';
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';
export type TicketCategory = 'billing' | 'technical' | 'shipping' | 'account' | 'other';
export type TicketEventType = 'status_change' | 'note' | 'reassignment' | 'credit_issued' | 'escalated';

export interface TicketResponse {
  id: string;
  customer_id: string;
  ticket_number: string;
  channel: TicketChannel;
  subject: string;
  status: TicketStatus;
  priority: TicketPriority;
  assigned_agent_id: string | null;
  category: TicketCategory;
  csat_score: number | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface TicketEventResponse {
  id: string;
  ticket_id: string;
  event_type: TicketEventType;
  actor: string;
  detail: string;
  created_at: string;
}

export interface TicketDetailResponse extends TicketResponse {
  events: TicketEventResponse[];
}

export interface TicketBoardColumn {
  status: TicketStatus;
  tickets: TicketResponse[];
}

export interface TicketBoardRow {
  channel: TicketChannel;
  columns: TicketBoardColumn[];
}
