import { useState, useEffect } from 'react';
import { agentsApi } from '../api/agents';
import type { AgentResponse, AgentTeam } from '../types';
import { Spinner, Avatar, Badge, StatusDot, EmptyState, Button, Modal, Input } from '../components/ui';
import { Users, PhoneCall, Clock, Mail, Plus, Pencil, UserX, UserCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';

const TEAMS: AgentTeam[] = ['general', 'billing', 'tech', 'onboarding'];
const ROLE_OPTIONS: { role: string; label: string }[] = [
  { role: 'support_agent', label: 'Support Agent' },
  { role: 'team_lead', label: 'Team Lead' },
];

const emptyCreateForm = {
  full_name: '',
  email: '',
  password: '',
  role: 'support_agent',
  role_label: 'Support Agent',
  team: 'general' as AgentTeam,
  shift_start: '09:00',
  shift_end: '17:00',
  extension: '',
};

export function Directory() {
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [teamFilter, setTeamFilter] = useState<AgentTeam | 'all'>('all');
  const { agent: me } = useAuth();
  const { toast } = useToast();
  const isTeamLead = me?.role === 'team_lead';

  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreateForm);
  const [creating, setCreating] = useState(false);

  const [editTarget, setEditTarget] = useState<AgentResponse | null>(null);
  const [editForm, setEditForm] = useState({ role: 'support_agent', role_label: '', team: 'general' as AgentTeam, shift_start: '', shift_end: '', extension: '' });
  const [savingEdit, setSavingEdit] = useState(false);

  const [togglingId, setTogglingId] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, [teamFilter]);

  const fetchAgents = () => {
    setLoading(true);
    agentsApi.list(teamFilter !== 'all' ? { team: teamFilter } : undefined)
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const openCreateModal = () => {
    setCreateForm(emptyCreateForm);
    setCreateOpen(true);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.full_name.trim() || !createForm.email.trim() || !createForm.password) return;
    setCreating(true);
    try {
      await agentsApi.create({
        full_name: createForm.full_name.trim(),
        email: createForm.email.trim(),
        password: createForm.password,
        role: createForm.role,
        team: createForm.team,
        shift_start: createForm.shift_start,
        shift_end: createForm.shift_end,
      });
      toast.success('Agent added');
      setCreateOpen(false);
      fetchAgents();
    } catch (e: any) {
      toast.error(e.message || 'Failed to add agent');
    } finally {
      setCreating(false);
    }
  };

  const openEditModal = (a: AgentResponse) => {
    setEditTarget(a);
    setEditForm({ role: a.role, role_label: a.role_label, team: a.team, shift_start: a.shift_start, shift_end: a.shift_end, extension: a.extension || '' });
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editTarget) return;
    setSavingEdit(true);
    try {
      const updated = await agentsApi.update(editTarget.id, {
        role: editForm.role,
        role_label: editForm.role_label,
        team: editForm.team,
        shift_start: editForm.shift_start,
        shift_end: editForm.shift_end,
        extension: editForm.extension || null,
      } as Partial<AgentResponse>);
      setAgents(prev => prev.map(a => a.id === updated.id ? updated : a));
      toast.success('Agent updated');
      setEditTarget(null);
    } catch (e: any) {
      toast.error(e.message || 'Failed to update agent');
    } finally {
      setSavingEdit(false);
    }
  };

  const handleToggleActive = async (a: AgentResponse) => {
    setTogglingId(a.id);
    try {
      if (a.active) {
        const updated = await agentsApi.delete(a.id); // soft-deactivate
        setAgents(prev => prev.map(x => x.id === updated.id ? updated : x));
        toast.success(`${a.full_name} deactivated`);
      } else {
        const updated = await agentsApi.update(a.id, { active: true } as Partial<AgentResponse>);
        setAgents(prev => prev.map(x => x.id === updated.id ? updated : x));
        toast.success(`${a.full_name} reactivated`);
      }
    } catch (e: any) {
      toast.error(e.message || 'Failed to update agent status');
    } finally {
      setTogglingId(null);
    }
  };

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 shrink-0 animate-fade-in-up">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
              <Users size={20} />
            </div>
            <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Agent Directory</h2>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Find team members and check availability.</p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="flex gap-2 p-1 bg-slate-100 dark:bg-gray-800 rounded-lg overflow-x-auto scrollbar-thin">
            {(['all', 'general', 'billing', 'tech', 'onboarding'] as const).map(t => (
              <button
                key={t}
                onClick={() => setTeamFilter(t)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize whitespace-nowrap transition-colors ${
                  teamFilter === t
                    ? 'bg-white dark:bg-gray-700 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 hover:bg-slate-200 dark:hover:bg-gray-700/50'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          {isTeamLead && (
            <Button onClick={openCreateModal} className="shrink-0"><Plus size={16} className="mr-1.5" /> Add Agent</Button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {agents.length === 0 ? (
          <EmptyState icon={Users} title="No agents found" description="No agents match the selected filters." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-6 stagger">
            {agents.map(agent => (
              <div key={agent.id} className={`card-interactive p-5 flex flex-col ${!agent.active ? 'opacity-60' : ''}`}>
                <div className="flex justify-between items-start mb-4 gap-4">
                  <div className="flex items-center gap-4">
                    <Avatar name={agent.full_name} size="lg" />
                    <div>
                      <h3 className="font-bold text-slate-900 dark:text-white">{agent.full_name}</h3>
                      <p className="text-xs font-medium text-brand-600 dark:text-brand-400 mt-0.5">{agent.role_label}</p>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <Badge variant={agent.team === 'billing' ? 'warning' : agent.team === 'tech' ? 'info' : 'neutral'} className="capitalize">{agent.team}</Badge>
                    {agent.active ? (
                      <StatusDot status={agent.on_duty ? 'online' : 'offline'} label={agent.on_duty ? 'On Duty' : 'Off Duty'} />
                    ) : (
                      <Badge variant="danger">Inactive</Badge>
                    )}
                  </div>
                </div>

                <div className="space-y-3 mt-2">
                  <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                    <Mail size={16} className="text-slate-400 shrink-0" />
                    <span className="truncate">{agent.email}</span>
                  </div>
                  {agent.extension && (
                    <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                      <PhoneCall size={16} className="text-slate-400 shrink-0" />
                      <span>Ext. {agent.extension}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
                    <Clock size={16} className="text-slate-400 shrink-0" />
                    <span>Shift: {agent.shift_start} - {agent.shift_end}</span>
                  </div>
                </div>

                {isTeamLead && (
                  <div className="flex justify-end gap-1 pt-4 mt-4 border-t border-slate-100 dark:border-gray-700">
                    <button onClick={() => openEditModal(agent)} title="Edit agent" className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-brand-900/20 rounded-md transition-colors">
                      <Pencil size={16} />
                    </button>
                    <button
                      onClick={() => handleToggleActive(agent)}
                      title={agent.active ? 'Deactivate agent' : 'Reactivate agent'}
                      disabled={togglingId === agent.id}
                      className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors disabled:opacity-50"
                    >
                      {agent.active ? <UserX size={16} /> : <UserCheck size={16} />}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={createOpen} onClose={() => !creating && setCreateOpen(false)} title="Add Agent">
        <form onSubmit={handleCreate} className="space-y-5">
          <Input label="Full Name" value={createForm.full_name} onChange={e => setCreateForm(f => ({ ...f, full_name: e.target.value }))} required />
          <Input label="Email" type="email" value={createForm.email} onChange={e => setCreateForm(f => ({ ...f, email: e.target.value }))} required />
          <Input label="Temporary Password" type="password" value={createForm.password} onChange={e => setCreateForm(f => ({ ...f, password: e.target.value }))} required />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Role</label>
              <select
                value={createForm.role}
                onChange={e => {
                  const role = e.target.value;
                  const label = ROLE_OPTIONS.find(r => r.role === role)?.label || 'Support Agent';
                  setCreateForm(f => ({ ...f, role, role_label: label }));
                }}
                className="input"
              >
                {ROLE_OPTIONS.map(r => <option key={r.role} value={r.role}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Team</label>
              <select value={createForm.team} onChange={e => setCreateForm(f => ({ ...f, team: e.target.value as AgentTeam }))} className="input">
                {TEAMS.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Shift Start" type="time" value={createForm.shift_start} onChange={e => setCreateForm(f => ({ ...f, shift_start: e.target.value }))} />
            <Input label="Shift End" type="time" value={createForm.shift_end} onChange={e => setCreateForm(f => ({ ...f, shift_end: e.target.value }))} />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setCreateOpen(false)} disabled={creating}>Cancel</Button>
            <Button type="submit" loading={creating} disabled={!createForm.full_name.trim() || !createForm.email.trim() || !createForm.password}>Add Agent</Button>
          </div>
        </form>
      </Modal>

      <Modal open={!!editTarget} onClose={() => !savingEdit && setEditTarget(null)} title={`Edit ${editTarget?.full_name ?? 'Agent'}`}>
        <form onSubmit={handleSaveEdit} className="space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Role</label>
              <select
                value={editForm.role}
                onChange={e => {
                  const role = e.target.value;
                  const label = ROLE_OPTIONS.find(r => r.role === role)?.label || editForm.role_label;
                  setEditForm(f => ({ ...f, role, role_label: label }));
                }}
                className="input"
              >
                {ROLE_OPTIONS.map(r => <option key={r.role} value={r.role}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Team</label>
              <select value={editForm.team} onChange={e => setEditForm(f => ({ ...f, team: e.target.value as AgentTeam }))} className="input">
                {TEAMS.map(t => <option key={t} value={t} className="capitalize">{t}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Shift Start" type="time" value={editForm.shift_start} onChange={e => setEditForm(f => ({ ...f, shift_start: e.target.value }))} />
            <Input label="Shift End" type="time" value={editForm.shift_end} onChange={e => setEditForm(f => ({ ...f, shift_end: e.target.value }))} />
          </div>
          <Input label="Extension" value={editForm.extension} onChange={e => setEditForm(f => ({ ...f, extension: e.target.value }))} />
          <p className="text-xs text-slate-400 dark:text-gray-500">On-duty status is derived automatically from shift hours.</p>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setEditTarget(null)} disabled={savingEdit}>Cancel</Button>
            <Button type="submit" loading={savingEdit}>Save Changes</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
