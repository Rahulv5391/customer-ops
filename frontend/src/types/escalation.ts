export type EscalationType = 'refund_approval' | 'sla_exception' | 'account_credit' | 'retention_offer_override';
export type EscalationPriority = 'low' | 'medium' | 'high' | 'urgent';
export type EscalationStatus = 'pending' | 'approved' | 'rejected';

export interface EscalationResponse {
  id: string;
  escalation_number: string;
  escalation_type: EscalationType;
  requested_action: string;
  priority: EscalationPriority;
  ticket_id: string;
  policy_citation: string | null;
  status: EscalationStatus;
  rejection_note: string | null;
  requested_by: string;
  created_at: string;
  resolved_at: string | null;
}
