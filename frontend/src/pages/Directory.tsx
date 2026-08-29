import { useState, useEffect } from 'react';
import { agentsApi } from '../api/agents';
import type { AgentResponse, AgentTeam } from '../types';
import { Spinner, Avatar, Badge, StatusDot, EmptyState } from '../components/ui';
import { Users, PhoneCall, Clock, Mail } from 'lucide-react';

export function Directory() {
  const [agents, setAgents] = useState<AgentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [teamFilter, setTeamFilter] = useState<AgentTeam | 'all'>('all');

  useEffect(() => {
    setLoading(true);
    agentsApi.list(teamFilter !== 'all' ? { team: teamFilter } : undefined)
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [teamFilter]);

  if (loading) return <div className="h-full flex items-center justify-center"><Spinner size="lg" /></div>;

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 shrink-0">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
              <Users size={20} />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Agent Directory</h2>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Find team members and check availability.</p>
        </div>
        
        <div className="flex gap-2 p-1 bg-slate-100 dark:bg-gray-800 rounded-lg shrink-0 overflow-x-auto scrollbar-thin">
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
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {agents.length === 0 ? (
          <EmptyState icon={Users} title="No agents found" description="No agents match the selected filters." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-6">
            {agents.map(agent => (
              <div key={agent.id} className="card-surface p-5 flex flex-col dark:bg-gray-800 dark:border-gray-700">
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
                    <StatusDot status={agent.on_duty ? 'online' : 'offline'} label={agent.on_duty ? 'On Duty' : 'Off Duty'} />
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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
