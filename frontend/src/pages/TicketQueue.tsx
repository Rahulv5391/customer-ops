import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketsApi } from '../api/tickets';
import type { TicketBoardRow, TicketStatus } from '../types';
import { Spinner, Avatar, Badge } from '../components/ui';
import { Inbox, MessageSquare, Phone, Globe, AlertCircle } from 'lucide-react';

const channelIcons: Record<string, any> = {
  email: Inbox,
  chat: MessageSquare,
  phone: Phone,
  social: Globe
};

const statusColors: Record<TicketStatus, string> = {
  unassigned: 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700',
  in_progress: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
  pending_qa: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
  resolved: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800',
  closed: 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 opacity-75'
};

export function TicketQueue() {
  const [board, setBoard] = useState<TicketBoardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    ticketsApi.board().then(setBoard).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="mb-6 shrink-0">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Ticket Queue</h2>
        <p className="text-sm text-slate-500 dark:text-gray-400">Manage incoming support requests across channels</p>
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin">
        <div className="flex flex-col gap-8 min-w-max pb-6">
          {board.map(row => {
            const Icon = channelIcons[row.channel] || MessageSquare;
            return (
              <div key={row.channel} className="flex flex-col">
                <div className="flex items-center gap-2 mb-4 sticky left-0 w-max">
                  <Icon size={20} className="text-brand-600 dark:text-brand-400" />
                  <h3 className="text-lg font-semibold text-slate-700 dark:text-slate-200 capitalize">{row.channel} Channel</h3>
                </div>
                <div className="flex gap-4 sm:gap-6 items-stretch">
                  {row.columns.map(col => (
                    <div key={col.status} className={`w-72 sm:w-80 shrink-0 rounded-2xl border p-4 flex flex-col ${statusColors[col.status]}`}>
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                          {col.status.replace('_', ' ')}
                        </span>
                        <Badge variant="neutral">{col.tickets.length}</Badge>
                      </div>
                      <div className="flex flex-col gap-3">
                        {col.tickets.map(t => (
                          <div 
                            key={t.id} 
                            onClick={() => navigate(`/tickets/${t.id}`)}
                            className="bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-gray-700 cursor-pointer hover:border-brand-400 dark:hover:border-brand-500 hover:shadow-md transition-all group"
                          >
                            <div className="flex justify-between items-start mb-2 gap-2">
                              <span className="text-xs font-medium text-slate-500 dark:text-gray-400 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">#{t.ticket_number}</span>
                              {t.priority === 'urgent' && <AlertCircle size={14} className="text-red-500 shrink-0" />}
                            </div>
                            <div className="font-medium text-sm text-slate-900 dark:text-white mb-4 line-clamp-2">{t.subject}</div>
                            <div className="flex items-center justify-between mt-auto">
                              <Badge variant={t.priority === 'high' || t.priority === 'urgent' ? 'danger' : t.priority === 'medium' ? 'warning' : 'neutral'}>{t.priority}</Badge>
                              {t.assigned_agent_id ? <Avatar name="Agent" size="sm" className="w-6 h-6 text-[10px]" /> : <span className="text-slate-400 dark:text-slate-500 text-[10px] font-semibold uppercase tracking-wide">Unassigned</span>}
                            </div>
                          </div>
                        ))}
                        {col.tickets.length === 0 && (
                          <div className="text-center p-6 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl text-slate-400 dark:text-slate-500 text-sm font-medium">
                            No tickets
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
