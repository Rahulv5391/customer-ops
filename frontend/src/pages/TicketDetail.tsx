import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketsApi } from '../api/tickets';
import type { TicketDetailResponse } from '../types';
import { Spinner, Badge, Button, Avatar, Input } from '../components/ui';
import { ArrowLeft, Clock, AlertTriangle } from 'lucide-react';

import { useToast } from '../hooks/useToast';

export function TicketDetail() {
  const { id } = useParams<{id: string}>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [ticket, setTicket] = useState<TicketDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState('');
  const [savingNote, setSavingNote] = useState(false);
  

  useEffect(() => {
    if (!id) return;
    ticketsApi.get(id).then(setTicket).catch(console.error).finally(() => setLoading(false));
  }, [id]);

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
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6 shrink-0">
        <button onClick={() => navigate(-1)} className="p-2 -ml-2 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 transition self-start sm:self-auto">
          <ArrowLeft size={20} className="text-slate-600 dark:text-gray-400" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-3 mb-1">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white truncate">#{ticket.ticket_number}</h2>
            <Badge variant="neutral" className="uppercase">{ticket.status.replace('_', ' ')}</Badge>
            <Badge variant={ticket.priority === 'urgent' ? 'danger' : ticket.priority === 'high' ? 'warning' : 'neutral'}>{ticket.priority}</Badge>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 truncate">{ticket.subject}</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0 overflow-hidden">
        {/* Sidebar Info */}
        <div className="lg:w-1/3 xl:w-1/4 flex flex-col gap-4 shrink-0 overflow-y-auto scrollbar-thin">
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
                <div className="flex items-center gap-2">
                  {ticket.assigned_agent_id ? (
                    <>
                      <Avatar name="Assigned Agent" size="sm" />
                      <span className="font-medium text-slate-900 dark:text-slate-100 hidden sm:inline">Assigned</span>
                    </>
                  ) : (
                    <span className="text-slate-400 dark:text-gray-500 italic">Unassigned</span>
                  )}
                </div>
              </div>
            </div>
            <div className="mt-6 flex flex-col gap-3">
              <Button variant="secondary" className="w-full">Reassign Ticket</Button>
              <Button variant="primary" className="w-full">Update Status</Button>
            </div>
          </div>
        </div>

        {/* Timeline Area */}
        <div className="lg:w-2/3 xl:w-3/4 flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-slate-200 dark:border-gray-700 overflow-hidden flex-1">
          <div className="p-4 sm:p-5 border-b border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800/80 shrink-0">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200">Event Timeline</h3>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
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
    </div>
  );
}
