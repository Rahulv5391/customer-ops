import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketsApi } from '../api/tickets';
import { agentsApi } from '../api/agents';
import type { TicketDetailResponse, TicketStatus, AgentResponse } from '../types';
import { Spinner, Badge, Button, Avatar, Input, Modal } from '../components/ui';
import { ArrowLeft, Clock, AlertTriangle, Mail, Phone, Building, ExternalLink } from 'lucide-react';

import { useToast } from '../hooks/useToast';

const STATUS_OPTIONS: TicketStatus[] = ['unassigned', 'in_progress', 'pending_qa', 'resolved', 'closed'];

export function TicketDetail() {
  const { id } = useParams<{id: string}>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [ticket, setTicket] = useState<TicketDetailResponse | null>(null);
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);

  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus>('unassigned');
  const [savingStatus, setSavingStatus] = useState(false);

  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState('');
  const [savingReassign, setSavingReassign] = useState(false);

  useEffect(() => {
    if (!id) return;
    Promise.all([ticketsApi.get(id), agentsApi.list()])
      .then(([t, a]) => { setTicket(t); setAgents(a); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const assignedAgent = agents.find(a => a.id === ticket?.assigned_agent_id);

  const openStatusModal = () => {
    if (!ticket) return;
    setSelectedStatus(ticket.status);
    setStatusModalOpen(true);
  };

  const openReassignModal = () => {
    if (!ticket) return;
    setSelectedAgentId(ticket.assigned_agent_id ?? '');
    setReassignModalOpen(true);
  };

  const handleUpdateStatus = async () => {
    if (!ticket || !id || selectedStatus === ticket.status) { setStatusModalOpen(false); return; }
    setSavingStatus(true);
    const previousStatus = ticket.status;
    try {
      const updated = await ticketsApi.update(id, { status: selectedStatus });
      const event = await ticketsApi.addEvent(id, {
        event_type: 'status_change',
        detail: `Status changed from ${previousStatus.replace('_', ' ')} to ${selectedStatus.replace('_', ' ')}.`,
      });
      setTicket(prev => prev ? { ...prev, status: updated.status, updated_at: updated.updated_at, events: [event, ...prev.events] } : prev);
      toast.success('Status updated');
      setStatusModalOpen(false);
    } catch (e: any) {
      toast.error(e.message || 'Failed to update status');
    } finally {
      setSavingStatus(false);
    }
  };

  const handleReassign = async () => {
    if (!ticket || !id) return;
    if (selectedAgentId === (ticket.assigned_agent_id ?? '')) { setReassignModalOpen(false); return; }
    setSavingReassign(true);
    try {
      const target = agents.find(a => a.id === selectedAgentId);
      const updated = await ticketsApi.update(id, { assigned_agent_id: selectedAgentId || null });
      const event = await ticketsApi.addEvent(id, {
        event_type: 'reassignment',
        detail: target ? `Reassigned to ${target.full_name} (${target.team} team).` : 'Unassigned.',
      });
      setTicket(prev => prev ? { ...prev, assigned_agent_id: updated.assigned_agent_id, events: [event, ...prev.events] } : prev);
      toast.success(target ? `Reassigned to ${target.full_name}` : 'Ticket unassigned');
      setReassignModalOpen(false);
    } catch (e: any) {
      toast.error(e.message || 'Failed to reassign ticket');
    } finally {
      setSavingReassign(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!note.trim() || !id) return;
    setSavingNote(true);
    try {
      const newEvent = await ticketsApi.addEvent(id, { event_type: 'note', detail: note });
      setTicket(prev => prev ? { ...prev, events: [newEvent, ...prev.events] } : null);
      setNote('');
      toast.success('Note added');
    } catch (e) {
      toast.error('Failed to add note');
    } finally {
      setSavingNote(false);
    }
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;
  if (!ticket) return <div className="text-center p-10 dark:text-white">Ticket not found</div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6 shrink-0 animate-fade-in-up">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 active:scale-90 transition-all self-start sm:self-auto">
          <ArrowLeft size={20} className="text-slate-600 dark:text-gray-400" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-3 mb-1">
            <h2 className="font-data text-xl sm:text-2xl font-bold text-slate-900 dark:text-white truncate">#{ticket.ticket_number}</h2>
            <Badge variant="neutral" className="uppercase">{ticket.status.replace('_', ' ')}</Badge>
            <Badge variant={ticket.priority === 'urgent' ? 'danger' : ticket.priority === 'high' ? 'warning' : 'neutral'}>{ticket.priority}</Badge>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 truncate">{ticket.subject}</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0 overflow-hidden">
        {/* Sidebar Info */}
        <div className="lg:w-1/3 xl:w-1/4 flex flex-col gap-4 shrink-0 overflow-y-auto scrollbar-thin">
          <div
            onClick={() => navigate(`/customers/${ticket.customer.id}`)}
            className="card-interactive p-5 dark:bg-gray-800 dark:border-gray-700"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wider">Customer</h3>
              <ExternalLink size={14} className="text-slate-400 dark:text-gray-500" />
            </div>
            <div className="flex items-center gap-3 mb-4">
              <Avatar name={ticket.customer.full_name} size="md" />
              <div className="min-w-0">
                <div className="font-semibold text-slate-900 dark:text-white truncate" title={ticket.customer.full_name}>{ticket.customer.full_name}</div>
                {ticket.customer.company && <div className="text-xs text-slate-500 dark:text-gray-400 truncate" title={ticket.customer.company}>{ticket.customer.company}</div>}
              </div>
            </div>
            <div className="space-y-2.5 text-sm">
              <div className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300 min-w-0">
                <Mail size={14} className="text-slate-400 shrink-0" />
                <span className="truncate" title={ticket.customer.email}>{ticket.customer.email}</span>
              </div>
              {ticket.customer.phone && (
                <div className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300">
                  <Phone size={14} className="text-slate-400 shrink-0" />
                  <span>{ticket.customer.phone}</span>
                </div>
              )}
              {ticket.customer.company && (
                <div className="flex items-center gap-2.5 text-slate-600 dark:text-slate-300 min-w-0">
                  <Building size={14} className="text-slate-400 shrink-0" />
                  <span className="truncate" title={ticket.customer.company}>{ticket.customer.company}</span>
                </div>
              )}
            </div>
          </div>

          <div className="card-surface p-5 dark:bg-gray-800 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-4 uppercase tracking-wider">Ticket Info</h3>
            <div className="space-y-4 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-gray-400">Channel</span>
                <span className="font-medium text-slate-900 dark:text-slate-100 capitalize">{ticket.channel}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-gray-400">Category</span>
                <span className="font-medium text-slate-900 dark:text-slate-100 capitalize">{ticket.category}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 dark:text-gray-400">Created</span>
                <span className="font-medium text-slate-900 dark:text-slate-100 text-right">{new Date(ticket.created_at).toLocaleDateString()}</span>
              </div>

              <div className="flex justify-between items-center pt-4 border-t border-slate-100 dark:border-gray-700">
                <span className="text-slate-500 dark:text-gray-400">Assignee</span>
                <div className="flex items-center gap-2 min-w-0">
                  {assignedAgent ? (
                    <>
                      <Avatar name={assignedAgent.full_name} size="sm" />
                      <span className="font-medium text-slate-900 dark:text-slate-100 truncate">{assignedAgent.full_name}</span>
                    </>
                  ) : ticket.assigned_agent_id ? (
                    <span className="text-slate-400 dark:text-gray-500 italic">Assigned</span>
                  ) : (
                    <span className="text-slate-400 dark:text-gray-500 italic">Unassigned</span>
                  )}
                </div>
              </div>
            </div>
            <div className="mt-6 flex flex-col gap-3">
              <Button variant="secondary" className="w-full" onClick={openReassignModal}>Reassign Ticket</Button>
              <Button variant="primary" className="w-full" onClick={openStatusModal}>Update Status</Button>
            </div>
          </div>
        </div>

        {/* Timeline Area */}
        <div className="lg:w-2/3 xl:w-3/4 flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700 overflow-hidden flex-1">
          <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800/80 shrink-0">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200">Event Timeline</h3>
          </div>

          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 stagger">
            {ticket.events.map(ev => (
              <div key={ev.id} className="flex gap-4">
                <div className="shrink-0 mt-1 hidden sm:block">
                  {ev.event_type === 'note' ? (
                    <Avatar name={ev.actor} size="sm" />
                  ) : ev.event_type === 'escalated' ? (
                    <div className="w-8 h-8 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center"><AlertTriangle size={14} className="text-red-600 dark:text-red-400" /></div>
                  ) : (
                    <div className="w-8 h-8 bg-slate-100 dark:bg-gray-700 rounded-full flex items-center justify-center"><Clock size={14} className="text-slate-400 dark:text-gray-400" /></div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">{ev.actor}</span>
                    <span className="text-xs text-slate-500 dark:text-gray-400">{new Date(ev.created_at).toLocaleString()}</span>
                  </div>
                  <div className={`text-sm mt-1 p-3 sm:p-4 rounded-xl ${
                    ev.event_type === 'note' ? 'bg-brand-50 dark:bg-brand-900/20 text-slate-800 dark:text-slate-200 border border-brand-100 dark:border-brand-800/30' :
                    ev.event_type === 'escalated' ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-100 dark:border-red-900/30 font-medium' :
                    'bg-slate-50 dark:bg-gray-700/50 text-slate-600 dark:text-slate-300'
                  }`}>
                    {ev.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 sm:p-5 border-t border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800/80 shrink-0">
            <form onSubmit={handleAddNote} className="flex flex-col sm:flex-row gap-3">
              <Input
                placeholder="Type an internal note..."
                value={note}
                onChange={e => setNote(e.target.value)}
                className="flex-1 bg-white dark:bg-gray-900 dark:border-gray-700"
              />
              <Button type="submit" loading={savingNote} disabled={!note.trim()} className="sm:w-auto w-full">Add Note</Button>
            </form>
          </div>
        </div>
      </div>

      <Modal open={statusModalOpen} onClose={() => !savingStatus && setStatusModalOpen(false)} title="Update Status" size="sm">
        <div className="space-y-5">
          <div>
            <label className="label">Status</label>
            <select
              value={selectedStatus}
              onChange={e => setSelectedStatus(e.target.value as TicketStatus)}
              className="input"
            >
              {STATUS_OPTIONS.map(s => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setStatusModalOpen(false)} disabled={savingStatus}>Cancel</Button>
            <Button type="button" loading={savingStatus} onClick={handleUpdateStatus}>Save</Button>
          </div>
        </div>
      </Modal>

      <Modal open={reassignModalOpen} onClose={() => !savingReassign && setReassignModalOpen(false)} title="Reassign Ticket" size="sm">
        <div className="space-y-5">
          <div>
            <label className="label">Agent</label>
            <select
              value={selectedAgentId}
              onChange={e => setSelectedAgentId(e.target.value)}
              className="input"
            >
              <option value="">Unassigned</option>
              {agents.filter(a => a.active).map(a => (
                <option key={a.id} value={a.id}>{a.full_name} — {a.team}{a.on_duty ? '' : ' (off duty)'}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setReassignModalOpen(false)} disabled={savingReassign}>Cancel</Button>
            <Button type="button" loading={savingReassign} onClick={handleReassign}>Save</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
