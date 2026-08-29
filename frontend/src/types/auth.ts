export type AgentRole = 'support_agent' | 'team_lead';
export type AgentTeam = 'billing' | 'tech' | 'onboarding' | 'general';

export interface AgentResponse {
  id: string;
  full_name: string;
  email: string;
  role: AgentRole;
  role_label: string;
  team: AgentTeam;
  shift_start: string;
  shift_end: string;
  on_duty: boolean;
  extension: string | null;
  active: boolean;
  two_factor: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
  agent: AgentResponse;
}
