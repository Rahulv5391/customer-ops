import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ticketsApi } from '../api/tickets';
import { customersApi } from '../api/customers';
import { agentsApi } from '../api/agents';
import type { TicketBoardRow, TicketStatus, TicketChannel, TicketCategory, TicketPriority, TicketResponse, CustomerResponse, AgentResponse } from '../types';
import { Spinner, Avatar, Badge, Button, Modal, Input } from '../components/ui';
import { Inbox, MessageSquare, Phone, Globe, AlertCircle, Plus } from 'lucide-react';
import { useToast } from '../hooks/useToast';

const channelIcons: Record<string, any> = {
  email: Inbox,
  chat: MessageSquare,
  phone: Phone,
  social: Globe
};

const STATUSES: TicketStatus[] = ['unassigned', 'in_progress', 'pending_qa', 'resolved', 'closed'];

const statusColors: Record<TicketStatus, string> = {
  unassigned: 'bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700',
  in_progress: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
  pending_qa: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
  resolved: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800',
  closed: 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 opacity-75'
};

const CHANNEL_OPTIONS: TicketChannel[] = ['email', 'chat', 'phone', 'social'];
const CATEGORY_OPTIONS: TicketCategory[] = ['billing', 'technical', 'shipping', 'account', 'other'];
const PRIORITY_OPTIONS: TicketPriority[] = ['low', 'medium', 'high', 'urgent'];

const emptyForm = {
  customerId: '',
  subject: '',
  channel: 'email' as TicketChannel,
  category: 'other' as TicketCategory,
  priority: 'medium' as TicketPriority,
};

export function TicketQueue() {
  const [board, setBoard] = useState<TicketBoardRow[]>([]);
  const [agentsById, setAgentsById] = useState<Record<string, AgentResponse>>({});
  const [loading, setLoading] = useState(true);
  const [channelFilter, setChannelFilter] = useState<TicketChannel | 'all'>('all');
  const navigate = useNavigate();
  const { toast } = useToast();

  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [customers, setCustomers] = useState<CustomerResponse[]>([]);
  const [customersLoading, setCustomersLoading] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [creating, setCreating] = useState(false);

  const fetchBoard = () => {
    setLoading(true);
    ticketsApi.board().then(setBoard).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchBoard();
    // The board only carries assigned_agent_id - fetch the directory once
    // so each ticket card can show the real assigned agent's initials
    // instead of a generic placeholder.
    agentsApi.list()
      .then(agents => setAgentsById(Object.fromEntries(agents.map(a => [a.id, a]))))
      .catch(console.error);
  }, []);

  // The API still returns one board row per channel (useful elsewhere) -
  // merge every channel's tickets into a single set of status columns here,
  // applying the channel filter, so the queue reads as one unified kanban
  // instead of a separate board per channel.
  const columns = useMemo(() => {
    const rows = channelFilter === 'all' ? board : board.filter(r => r.channel === channelFilter);
    return STATUSES.map(status => ({
      status,
      tickets: rows.flatMap(r => r.columns.find(c => c.status === status)?.tickets ?? []),
    }));
  }, [board, channelFilter]);

  const openCreateModal = () => {
    setForm(emptyForm);
    setCreateModalOpen(true);
    if (customers.length === 0) {
      setCustomersLoading(true);
      customersApi.list({ limit: 100 })
        .then(setCustomers)
        .catch(() => toast.error('Failed to load customers'))
        .finally(() => setCustomersLoading(false));
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customerId || !form.subject.trim()) return;
    setCreating(true);
    try {
      await ticketsApi.create({
        customer_id: form.customerId,
        subject: form.subject.trim(),
        channel: form.channel,
        category: form.category,
        priority: form.priority,
      });
      toast.success('Ticket created');
      setCreateModalOpen(false);
      fetchBoard();
    } catch (e: any) {
      toast.error(e.message || 'Failed to create ticket');
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 shrink-0 animate-fade-in-up">
        <div>
          <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Ticket Queue</h2>
          <p className="text-sm text-slate-500 dark:text-gray-400">Manage incoming support requests across channels</p>
        </div>
        <Button onClick={openCreateModal} className="shrink-0 w-full sm:w-auto">
          <Plus size={16} className="mr-1.5" /> New Ticket
        </Button>
      </div>

      <div className="flex gap-2 p-1 bg-slate-100 dark:bg-gray-800 rounded-lg mb-6 shrink-0 w-max overflow-x-auto scrollbar-thin">
        {(['all', ...CHANNEL_OPTIONS] as const).map(c => {
          const Icon = c === 'all' ? null : channelIcons[c];
          return (
            <button
              key={c}
              onClick={() => setChannelFilter(c)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold capitalize whitespace-nowrap transition-colors ${
                channelFilter === c
                  ? 'bg-white dark:bg-gray-700 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 hover:bg-slate-200 dark:hover:bg-gray-700/50'
              }`}
            >
              {Icon && <Icon size={13} />}
              {c === 'all' ? 'All Channels' : c}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-auto scrollbar-thin">
        <div className="flex gap-4 sm:gap-6 items-stretch min-w-max pb-6">
          {columns.map(col => (
            <div key={col.status} className={`w-72 sm:w-80 shrink-0 rounded-2xl border p-4 flex flex-col ${statusColors[col.status]}`}>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                  {col.status.replace('_', ' ')}
                </span>
                <Badge variant="neutral">{col.tickets.length}</Badge>
              </div>
              <div className="flex flex-col gap-3 stagger">
                {col.tickets.map((t: TicketResponse) => {
                  const assignedAgent = t.assigned_agent_id ? agentsById[t.assigned_agent_id] : null;
                  const ChannelIcon = channelIcons[t.channel] || MessageSquare;
                  return (
                    <div
                      key={t.id}
                      onClick={() => navigate(`/tickets/${t.id}`)}
                      className="card-interactive bg-white dark:bg-gray-800 p-4 group"
                    >
                      <div className="flex justify-between items-start mb-2 gap-2">
                        <div className="flex items-center gap-1.5 min-w-0">
                          <ChannelIcon size={12} className="text-slate-400 dark:text-gray-500 shrink-0" />
                          <span className="font-data text-xs font-medium text-slate-500 dark:text-gray-400 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors truncate">#{t.ticket_number}</span>
                        </div>
                        {t.priority === 'urgent' && <AlertCircle size={14} className="text-red-500 shrink-0" />}
                      </div>
                      <div className="font-medium text-sm text-slate-900 dark:text-white mb-4 line-clamp-2">{t.subject}</div>
                      <div className="flex items-center justify-between mt-auto">
                        <Badge variant={t.priority === 'high' || t.priority === 'urgent' ? 'danger' : t.priority === 'medium' ? 'warning' : 'neutral'}>{t.priority}</Badge>
                        {t.assigned_agent_id ? (
                          <div title={assignedAgent?.full_name ?? 'Assigned'}>
                            <Avatar name={assignedAgent?.full_name ?? '?'} size="sm" className="w-6 h-6 text-[10px]" />
                          </div>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500 text-[10px] font-semibold uppercase tracking-wide">Unassigned</span>
                        )}
                      </div>
                    </div>
                  );
                })}
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

      <Modal open={createModalOpen} onClose={() => !creating && setCreateModalOpen(false)} title="New Ticket" size="md">
        <form onSubmit={handleCreateTicket} className="space-y-5">
          <div>
            <label className="label">Customer</label>
            <select
              value={form.customerId}
              onChange={e => setForm(f => ({ ...f, customerId: e.target.value }))}
              className="input"
              disabled={customersLoading}
              required
            >
              <option value="" disabled>{customersLoading ? 'Loading customers…' : 'Select a customer'}</option>
              {customers.map(c => (
                <option key={c.id} value={c.id}>{c.full_name} — {c.email}</option>
              ))}
            </select>
          </div>

          <Input
            label="Subject"
            placeholder="e.g. Order never arrived"
            value={form.subject}
            onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
            required
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="label">Channel</label>
              <select
                value={form.channel}
                onChange={e => setForm(f => ({ ...f, channel: e.target.value as TicketChannel }))}
                className="input"
              >
                {CHANNEL_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Category</label>
              <select
                value={form.category}
                onChange={e => setForm(f => ({ ...f, category: e.target.value as TicketCategory }))}
                className="input"
              >
                {CATEGORY_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Priority</label>
              <select
                value={form.priority}
                onChange={e => setForm(f => ({ ...f, priority: e.target.value as TicketPriority }))}
                className="input"
              >
                {PRIORITY_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>

          <p className="text-xs text-slate-400 dark:text-gray-500">New tickets start unassigned — use Reassign Ticket on the ticket's detail page to assign one.</p>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setCreateModalOpen(false)} disabled={creating}>Cancel</Button>
            <Button type="submit" loading={creating} disabled={!form.customerId || !form.subject.trim()}>Create Ticket</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
