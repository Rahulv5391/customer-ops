import { useState, useEffect } from 'react';
import { activityLogApi } from '../api/activityLog';
import type { ActivityLogResponse } from '../types';
import { Spinner, EmptyState, Avatar } from '../components/ui';
import { ScrollText, Link as LinkIcon } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function ActivityLog() {
  const [logs, setLogs] = useState<ActivityLogResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    activityLogApi.list({ limit: 100 })
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  const navigateToEntity = (type: string, id: string) => {
    if (type === 'ticket') navigate(`/tickets/${id}`);
    else if (type === 'customer') navigate(`/customers/${id}`);
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="mb-6 shrink-0">
        <div className="flex items-center gap-3 mb-1">
          <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
            <ScrollText size={20} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">System Activity Log</h2>
        </div>
        <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Immutable audit trail of all agent actions and system events.</p>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700">
        {logs.length === 0 ? (
          <EmptyState icon={ScrollText} title="No Activity" description="No system activity has been recorded yet." />
        ) : (
          <div className="min-w-max">
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-900/50 sticky top-0 z-10 text-xs font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider">
              <div className="col-span-2 pl-2">Timestamp</div>
              <div className="col-span-3">Actor</div>
              <div className="col-span-2">Action</div>
              <div className="col-span-4">Summary</div>
              <div className="col-span-1 text-right pr-2">Entity</div>
            </div>
            
            <div className="divide-y divide-slate-100 dark:divide-gray-700/50">
              {logs.map(log => (
                <div key={log.id} className="grid grid-cols-12 gap-4 p-4 items-center hover:bg-slate-50 dark:hover:bg-gray-700/30 transition-colors group">
                  <div className="col-span-2 pl-2 text-xs text-slate-500 dark:text-gray-400">
                    {new Date(log.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </div>
                  <div className="col-span-3 flex items-center gap-3">
                    {log.actor.toLowerCase().includes('system') || log.actor === 'AI Assistant' ? (
                      <div className="w-6 h-6 bg-slate-100 dark:bg-gray-700 rounded-full flex items-center justify-center shrink-0">
                        <span className="text-[10px] font-bold text-slate-500 dark:text-gray-400">SYS</span>
                      </div>
                    ) : (
                      <Avatar name={log.actor} size="sm" className="w-6 h-6 text-[10px]" />
                    )}
                    <span className="text-sm font-medium text-slate-900 dark:text-slate-200 truncate">{log.actor}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-xs font-semibold px-2 py-1 bg-slate-100 dark:bg-gray-700 text-slate-600 dark:text-gray-300 rounded uppercase tracking-wider">
                      {log.action_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="col-span-4 text-sm text-slate-700 dark:text-slate-300 truncate" title={log.summary}>
                    {log.summary}
                  </div>
                  <div className="col-span-1 flex justify-end pr-2">
                    {['ticket', 'customer'].includes(log.entity_type) ? (
                      <button 
                        onClick={() => navigateToEntity(log.entity_type, log.entity_id)}
                        className="p-1.5 text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-900/30 rounded transition opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title={`View ${log.entity_type}`}
                      >
                        <LinkIcon size={16} />
                      </button>
                    ) : (
                      <span className="text-xs text-slate-400 dark:text-gray-500 capitalize">{log.entity_type}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
