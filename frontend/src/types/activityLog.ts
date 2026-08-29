export interface ActivityLogResponse {
  id: string;
  action_type: string;
  actor: string;
  entity_type: string;
  entity_id: string;
  summary: string;
  created_at: string;
}
