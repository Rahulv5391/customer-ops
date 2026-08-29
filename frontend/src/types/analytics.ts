export interface TicketVolumePoint {
  date: string;
  count: number;
}

export interface TopIssueCategory {
  category: string;
  count: number;
}

export interface AnalyticsSummary {
  ticket_volume_7d: TicketVolumePoint[];
  avg_resolution_time_hours: number | null;
  csat_average: number | null;
  deflection_rate: number | null;
}
