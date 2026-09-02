import { useState, useEffect } from 'react';
import { activityLogApi } from '../api/activityLog';
import type { ActivityLogResponse } from '../types';
import { Spinner, EmptyState, Avatar, Button } from '../components/ui';
import { ScrollText, Link as LinkIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ENTITY_TYPES = ['ticket', 'customer', 'escalation', 'agent', 'kb_document', 'data_source'];
const PAGE_SIZE = 50;

export function ActivityLog() {
  const [logs, setLogs] = useState<ActivityLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [entityType, setEntityType] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    activityLogApi.list({ limit: PAGE_SIZE, entity_type: entityType || undefined })
      .then(res => {
        setLogs(res);
        setHasMore(res.length === PAGE_SIZE);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [entityType]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const res = await activityLogApi.list({ limit: PAGE_SIZE, offset: logs.length, entity_type: entityType || undefined });
      setLogs(prev => [...prev, ...res]);
      setHasMore(res.length === PAGE_SIZE);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingMore(false);
    }
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  const navigateToEntity = (type: string, id: string) => {
    if (type === 'ticket') navigate(`/tickets/${id}`);
    else if (type === 'customer') navigate(`/customers/${id}`);
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="mb-6 shrink-0 animate-fade-in-up flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
              <ScrollText size={20} />
            </div>
            <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">System Activity Log</h2>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Audit trail of agent actions and system events.</p>
        </div>
        <select
          value={entityType}
          onChange={e => setEntityType(e.target.value)}
          className="px-3 py-2 rounded-lg border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-slate-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition capitalize"
        >
          <option value="">All Entities</option>
          {ENTITY_TYPES.map(t => <option key={t} value={t} className="capitalize">{t.replace('_', ' ')}</option>)}
        </select>
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700 animate-fade-in-up" style={{ animationDelay: '80ms' }}>
        {logs.length === 0 ? (
          <EmptyState icon={ScrollText} title="No Activity" description="No system activity has been recorded yet." />
        ) : (
          <div className="min-w-[900px]">
            {/* Explicit per-column widths (not grid-cols-12 fractions) - a
                12-track grid with no intrinsic sizing just stretches every
                column to an equal share of the full panel width, leaving
                huge gaps around short content like a timestamp or a name.
                Only Summary should actually grow, so it's the lone `1fr`. */}
            <div className="grid grid-cols-[165px_170px_190px_1fr_110px] gap-4 p-4 items-center border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-900/50 sticky top-0 z-10 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">
              <div className="pl-2">Timestamp</div>
              <div>Actor</div>
              <div>Action</div>
              <div>Summary</div>
              <div className="text-right pr-2">Entity</div>
            </div>

            <div className="divide-y divide-slate-100 dark:divide-gray-700/50">
              {logs.map(log => (
                <div key={log.id} className="grid grid-cols-[165px_170px_190px_1fr_110px] gap-4 p-4 items-start hover:bg-slate-50 dark:hover:bg-gray-700/30 transition-colors group">
                  <div className="pl-2 font-data text-xs text-slate-500 dark:text-gray-400 whitespace-nowrap">
                    {new Date(log.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </div>
                  <div className="flex items-center gap-3 min-w-0">
                    {log.actor.toLowerCase().includes('system') || log.actor === 'AI Assistant' ? (
                      <div className="w-6 h-6 bg-slate-100 dark:bg-gray-700 rounded-full flex items-center justify-center shrink-0">
                        <span className="text-[10px] font-bold text-slate-500 dark:text-gray-400">SYS</span>
                      </div>
                    ) : (
                      <Avatar name={log.actor} size="sm" className="w-6 h-6 text-[10px]" />
                    )}
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-200 truncate">{log.actor}</span>
                  </div>
                  <div>
                    <span className="text-xs font-semibold px-2 py-1 bg-slate-100 dark:bg-gray-700 text-slate-600 dark:text-gray-300 rounded uppercase tracking-wider whitespace-nowrap">
                      {log.action_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="min-w-0 text-sm text-slate-700 dark:text-slate-300 break-words">
                    {log.summary}
                  </div>
                  <div className="min-w-0 flex justify-end pr-2">
                    {['ticket', 'customer'].includes(log.entity_type) ? (
                      <button
                        onClick={() => navigateToEntity(log.entity_type, log.entity_id)}
                        className="p-1.5 text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/30 rounded transition opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title={`View ${log.entity_type}`}
                      >
                        <LinkIcon size={16} />
                      </button>
                    ) : (
                      <span className="text-xs text-slate-400 dark:text-gray-500 capitalize truncate">{log.entity_type.replace(/_/g, ' ')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {hasMore && (
        <div className="shrink-0 flex justify-center pt-4">
          <Button variant="secondary" onClick={loadMore} loading={loadingMore}>Load More</Button>
        </div>
      )}
    </div>
  );
}
