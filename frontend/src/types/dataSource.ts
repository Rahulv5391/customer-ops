export type ConnectorType = 'zendesk' | 'salesforce' | 'shopify' | 'slack' | 'kb_repo';
export type SyncStatus = 'healthy' | 'degraded' | 'error';

export interface DataSourceResponse {
  id: string;
  name: string;
  connector_type: ConnectorType;
  sync_status: SyncStatus;
  sync_health_pct: number;
  tables_schema: string;
  sync_logs: string;
  last_synced_at: string;
}
