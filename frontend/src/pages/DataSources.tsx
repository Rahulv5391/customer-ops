import { useState, useEffect } from 'react';
import { dataSourcesApi } from '../api/dataSources';
import type { DataSourceResponse } from '../types';
import { Spinner, Button, EmptyState, StatusDot, Modal, Input } from '../components/ui';
import { useToast } from '../hooks/useToast';
import { Database, RefreshCw, Trash2, Server } from 'lucide-react';

const CONNECTOR_TYPES = ['zendesk', 'salesforce', 'shopify', 'slack', 'kb_repo'];

export function DataSources() {
  const [sources, setSources] = useState<DataSourceResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const { toast } = useToast();

  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ name: '', connector_type: 'zendesk' });
  const [creating, setCreating] = useState(false);

  const [deleteTarget, setDeleteTarget] = useState<DataSourceResponse | null>(null);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = () => {
    setLoading(true);
    dataSourcesApi.list()
      .then(setSources)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const handleSync = async (id: string) => {
    setSyncingId(id);
    try {
      await dataSourcesApi.sync(id);
      toast.success('Sync triggered successfully');
      fetchSources();
    } catch (e: any) {
      toast.error(e.message || 'Sync failed');
    } finally {
      setSyncingId(null);
    }
  };

  const openCreateModal = () => {
    setForm({ name: '', connector_type: 'zendesk' });
    setCreateOpen(true);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setCreating(true);
    try {
      await dataSourcesApi.create({ name: form.name.trim(), connector_type: form.connector_type });
      toast.success('Data source connected');
      setCreateOpen(false);
      fetchSources();
    } catch (e: any) {
      toast.error(e.message || 'Failed to connect data source');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeletingId(deleteTarget.id);
    try {
      await dataSourcesApi.delete(deleteTarget.id);
      toast.success('Data source removed');
      setSources(prev => prev.filter(s => s.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (e: any) {
      toast.error(e.message || 'Failed to remove data source');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 shrink-0 animate-fade-in-up">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
              <Database size={20} />
            </div>
            <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Data Sources</h2>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Manage external system connections and sync status.</p>
        </div>
        <Button onClick={openCreateModal} className="shrink-0"><Server size={16} className="mr-2 hidden sm:block" /><span className="sm:hidden">Connect</span><span className="hidden sm:inline">Connect New Source</span></Button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {sources.length === 0 ? (
          <EmptyState icon={Database} title="No Data Sources" description="Connect your first external system to start syncing data." />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-6 stagger">
            {sources.map(source => (
              <div key={source.id} className="card-surface p-5 flex flex-col">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-1.5">{source.name}</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider">{source.connector_type}</span>
                      <span className="text-slate-300 dark:text-gray-600">•</span>
                      <StatusDot status={source.sync_status} label={source.sync_status} />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-brand-600 dark:text-brand-400">
                    {source.sync_health_pct}%
                  </div>
                </div>

                <div className="space-y-3 text-sm mb-6 flex-1 bg-slate-50 dark:bg-gray-900/50 p-4 rounded-xl border border-slate-100 dark:border-gray-700">
                  <div className="flex justify-between">
                    <span className="text-slate-500 dark:text-gray-400 font-medium">Last Synced</span>
                    <span className="font-medium text-slate-900 dark:text-slate-200">
                      {source.last_synced_at ? new Date(source.last_synced_at).toLocaleString() : 'Never'}
                    </span>
                  </div>
                  <div className="flex justify-between items-start">
                    <span className="text-slate-500 dark:text-gray-400 font-medium pt-0.5">Synced Tables</span>
                    <span className="font-medium text-slate-900 dark:text-slate-200 text-right max-w-[60%] line-clamp-2" title={source.tables_schema}>{source.tables_schema}</span>
                  </div>
                </div>

                <div className="flex justify-between items-center gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
                  <button
                    onClick={() => setDeleteTarget(source)}
                    title="Remove data source"
                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <Trash2 size={18} />
                  </button>
                  <Button
                    variant="secondary"
                    onClick={() => handleSync(source.id)}
                    loading={syncingId === source.id}
                    disabled={syncingId !== null}
                    className="w-full sm:w-auto"
                  >
                    <RefreshCw size={16} className={`mr-2 ${syncingId === source.id ? 'animate-spin' : ''}`} />
                    Sync Now
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={createOpen} onClose={() => !creating && setCreateOpen(false)} title="Connect New Source" size="sm">
        <form onSubmit={handleCreate} className="space-y-5">
          <Input
            label="Source Name"
            placeholder="e.g. Zendesk"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            required
          />
          <div>
            <label className="label">Connector Type</label>
            <select
              value={form.connector_type}
              onChange={e => setForm(f => ({ ...f, connector_type: e.target.value }))}
              className="input capitalize"
            >
              {CONNECTOR_TYPES.map(t => <option key={t} value={t} className="capitalize">{t.replace('_', ' ')}</option>)}
            </select>
          </div>
          <p className="text-xs text-slate-400 dark:text-gray-500">This registers the connector - it doesn't make a live connection. Use "Sync Now" afterward to simulate a sync.</p>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setCreateOpen(false)} disabled={creating}>Cancel</Button>
            <Button type="submit" loading={creating} disabled={!form.name.trim()}>Connect</Button>
          </div>
        </form>
      </Modal>

      <Modal open={!!deleteTarget} onClose={() => !deletingId && setDeleteTarget(null)} title="Remove Data Source" size="sm">
        <div className="space-y-5">
          <p className="text-sm text-slate-600 dark:text-gray-400">
            Remove <span className="font-semibold text-slate-900 dark:text-white">{deleteTarget?.name}</span>? This stops any future syncs - it can't be undone.
          </p>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)} disabled={deletingId !== null}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} loading={deletingId === deleteTarget?.id}>Remove</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
