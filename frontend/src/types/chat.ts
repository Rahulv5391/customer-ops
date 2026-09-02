export type ChatMessageType = 'text' | 'action-confirmation' | 'citation-answer' | 'error';
export type ActionType = 'update_field' | 'reassign_ticket' | 'schedule_callback' | 'create_escalation';

export interface Citation {
  document_title: string;
  version: string;
  source_updated_at: string;
  section: string | null;
  snippet: string | null;
}

export interface PendingAction {
  token: string;
  action_type: ActionType;
  entity_type: string;
  entity_id: string;
  field_name: string | null;
  field_value: string | null;
  escalation_payload: Record<string, unknown> | null;
}

export interface ChatMessage {
  type: ChatMessageType;
  content: string;
  action_diff: {
    before: Record<string, unknown>;
    after: Record<string, unknown>;
  } | null;
  pending_action: PendingAction | null;
  citations: Citation[] | null;
  status: 'final' | 'pending_confirmation' | null;
  resolved_entity_id: string | null;
  resolved_entity_type: string | null;
}

export interface ChatConfirmResponse {
  success: boolean;
  message: string;
  entity: Record<string, unknown>;
}

export interface UIChatMessage {
  id: string;
  fromUser: boolean;
  userText?: string;
  type: ChatMessageType;
  content: string;
  action_diff: { before: Record<string, unknown>; after: Record<string, unknown> } | null;
  pending_action: PendingAction | null;
  citations: Citation[] | null;
  status: 'final' | 'pending_confirmation' | null;
  resolved_entity_id: string | null;
  resolved_entity_type: string | null;
}
