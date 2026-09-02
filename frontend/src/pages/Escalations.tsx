import { useState, useEffect } from 'react';
import { escalationsApi } from '../api/escalations';
import type { EscalationResponse } from '../types';
import { Spinner, Badge, Button, EmptyState, Modal } from '../components/ui';
import { useToast } from '../hooks/useToast';
import { ShieldCheck, AlertTriangle, Check, X, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

type Tab = 'pending' | 'resolved';

export function Escalations() {
  const [tab, setTab] = useState<Tab>('pending');
  const [escalations, setEscalations] = useState<EscalationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [rejectTarget, setRejectTarget] = useState<EscalationResponse | null>(null);
  const [rejectNote, setRejectNote] = useState('');
  const { toast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    fetchEscalations();
  }, [tab]);

  const fetchEscalations = async () => {
    setLoading(true);
    try {
      if (tab === 'pending') {
        setEscalations(await escalationsApi.list({ status: 'pending' }));
      } else {
        // No combined "resolved" status server-side - approved and
        // rejected are both terminal states, so merge the two lists.
        const [approved, rejected] = await Promise.all([
          escalationsApi.list({ status: 'approved' }),
          escalationsApi.list({ status: 'rejected' }),
        ]);
        setEscalations(
          [...approved, ...rejected].sort((a, b) =>
            new Date(b.resolved_at ?? b.created_at).getTime() - new Date(a.resolved_at ?? a.created_at).getTime()
          )
        );
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (id: string, status: 'approved' | 'rejected', rejectionNote?: string) => {
    setResolvingId(id);
    try {
      await escalationsApi.resolve(id, { status, rejection_note: rejectionNote });
      toast.success(`Escalation ${status}`);
      setEscalations(prev => prev.filter(e => e.id !== id));
    } catch (e: any) {
      toast.error(e.message || 'Failed to resolve escalation');
    } finally {
      setResolvingId(null);
    }
  };

  const openRejectModal = (esc: EscalationResponse) => {
    setRejectTarget(esc);
    setRejectNote('');
  };

  const confirmReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectTarget) return;
    await handleResolve(rejectTarget.id, 'rejected', rejectNote.trim() || undefined);
    setRejectTarget(null);
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="mb-6 shrink-0 animate-fade-in-up">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
                <ShieldCheck size={20} />
              </div>
              <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Escalation Queue</h2>
            </div>
            <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Review and approve actions that require Team Lead authorization.</p>
          </div>
          <div className="flex gap-2 p-1 bg-slate-100 dark:bg-gray-800 rounded-lg shrink-0">
            {(['pending', 'resolved'] as const).map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize whitespace-nowrap transition-colors ${
                  tab === t
                    ? 'bg-white dark:bg-gray-700 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 hover:bg-slate-200 dark:hover:bg-gray-700/50'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {escalations.length === 0 ? (
          <EmptyState
            icon={ShieldCheck}
            title={tab === 'pending' ? 'All Caught Up' : 'No Resolved Escalations'}
            description={tab === 'pending' ? 'There are no pending escalations requiring your review.' : 'Approved and rejected escalations will show up here.'}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-6 stagger">
            {escalations.map(esc => (
              <div key={esc.id} className="card-surface p-5 flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-data text-sm font-bold text-slate-900 dark:text-white">{esc.escalation_number}</span>
                      <Badge variant={esc.priority === 'urgent' ? 'danger' : esc.priority === 'high' ? 'warning' : 'neutral'}>{esc.priority}</Badge>
                      {tab === 'resolved' && (
                        <Badge variant={esc.status === 'approved' ? 'success' : 'danger'} className="capitalize">{esc.status}</Badge>
                      )}
                    </div>
                    <span className="text-[10px] font-bold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/20 px-2 py-0.5 rounded uppercase tracking-wider">{esc.escalation_type.replace(/_/g, ' ')}</span>
                  </div>
                  {esc.priority === 'urgent' && <AlertTriangle size={20} className="text-red-500 shrink-0" />}
                </div>

                <div className="flex-1 mb-6">
                  <div className="text-sm text-slate-700 dark:text-slate-300 font-medium mb-4 bg-slate-50 dark:bg-gray-900 p-3 rounded-lg border border-slate-100 dark:border-gray-700 italic">
                    "{esc.requested_action}"
                  </div>

                  <div className="space-y-3 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500 dark:text-gray-400 font-medium">Requested By</span>
                      <span className="font-semibold text-slate-900 dark:text-slate-200">{esc.requested_by}</span>
                    </div>
                    <div className="flex justify-between items-start">
                      <span className="text-slate-500 dark:text-gray-400 font-medium">Policy Citation</span>
                      <span className="font-medium text-slate-900 dark:text-slate-200 text-right max-w-[60%] line-clamp-2" title={esc.policy_citation || 'None'}>{esc.policy_citation || 'None'}</span>
                    </div>
                    {tab === 'resolved' && esc.status === 'rejected' && esc.rejection_note && (
                      <div className="flex justify-between items-start">
                        <span className="text-slate-500 dark:text-gray-400 font-medium">Rejection Reason</span>
                        <span className="font-medium text-slate-900 dark:text-slate-200 text-right max-w-[60%] line-clamp-3">{esc.rejection_note}</span>
                      </div>
                    )}
                    {tab === 'resolved' && esc.resolved_at && (
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 dark:text-gray-400 font-medium">Resolved</span>
                        <span className="font-medium text-slate-900 dark:text-slate-200">{new Date(esc.resolved_at).toLocaleString()}</span>
                      </div>
                    )}
                    <div className="flex justify-between items-center pt-3 mt-3 border-t border-slate-100 dark:border-gray-700">
                      <span className="text-slate-500 dark:text-gray-400 font-medium">Related Ticket</span>
                      <button
                        onClick={() => navigate(`/tickets/${esc.ticket_id}`)}
                        className="flex items-center gap-1 text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 hover:underline font-semibold transition-colors"
                      >
                        View Details <ExternalLink size={12} />
                      </button>
                    </div>
                  </div>
                </div>

                {tab === 'pending' && (
                  <div className="flex gap-3 mt-auto pt-4 border-t border-slate-100 dark:border-gray-700">
                    <Button
                      variant="danger"
                      className="flex-1 bg-red-50 text-red-600 hover:bg-red-100 border border-red-100 dark:bg-red-900/10 dark:hover:bg-red-900/30 dark:border-red-900/30 dark:text-red-400 transition-colors"
                      onClick={() => openRejectModal(esc)}
                      loading={resolvingId === esc.id}
                      disabled={resolvingId !== null}
                    >
                      <X size={16} /> Reject
                    </Button>
                    <Button
                      variant="primary"
                      className="flex-1 bg-emerald-500 hover:bg-emerald-600 border-none shadow-sm shadow-emerald-500/20"
                      onClick={() => handleResolve(esc.id, 'approved')}
                      loading={resolvingId === esc.id}
                      disabled={resolvingId !== null}
                    >
                      <Check size={16} /> Approve
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={!!rejectTarget} onClose={() => resolvingId === null && setRejectTarget(null)} title="Reject Escalation" size="sm">
        <form onSubmit={confirmReject} className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-gray-400">
            Rejecting <span className="font-semibold text-slate-900 dark:text-white">{rejectTarget?.escalation_number}</span>. This note is visible to {rejectTarget?.requested_by}.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-gray-400 mb-1.5 uppercase tracking-wide">Reason (optional)</label>
            <textarea
              value={rejectNote}
              onChange={e => setRejectNote(e.target.value)}
              rows={3}
              placeholder="e.g. Outside policy - amount exceeds the approved goodwill limit."
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-slate-800 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/25 focus:border-brand-500 transition"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setRejectTarget(null)} disabled={resolvingId !== null}>Cancel</Button>
            <Button type="submit" variant="danger" loading={resolvingId === rejectTarget?.id}>Reject Escalation</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
