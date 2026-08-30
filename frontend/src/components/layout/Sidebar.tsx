import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Inbox, BookOpen, UserSquare2, AlertTriangle, Database, ScrollText, LogOut } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { Avatar, Badge } from '../ui';

interface SidebarProps {
  open: boolean;
  pendingEscalations: number;
}

const navItems = [
  { id: 'dashboard',       path: '/dashboard',      label: 'Dashboard',       icon: LayoutDashboard },
  { id: 'customers',       path: '/customers',      label: 'Customers',       icon: Users },
  { id: 'tickets',         path: '/tickets',        label: 'Ticket Queue',    icon: Inbox },
  { id: 'knowledge-base',  path: '/knowledge-base', label: 'Knowledge Base',  icon: BookOpen },
  { id: 'directory',       path: '/directory',      label: 'Agent Directory', icon: UserSquare2 },
  { id: 'escalations',     path: '/escalations',    label: 'Escalations',     icon: AlertTriangle, teamLeadOnly: true },
  { id: 'data-sources',    path: '/data-sources',   label: 'Data Sources',    icon: Database,      teamLeadOnly: true },
  { id: 'activity-log',    path: '/activity-log',   label: 'Activity Log',    icon: ScrollText,    teamLeadOnly: true },
];

export function Sidebar({ open, pendingEscalations }: SidebarProps) {
  const { agent, logout } = useAuth();
  if (!agent) return null;

  const isTeamLead = agent.role === 'team_lead';
  const visibleItems = navItems.filter(item => !item.teamLeadOnly || isTeamLead);

  return (
    <aside className={`bg-white dark:bg-gray-800 border-r border-slate-200 dark:border-gray-700 flex flex-col transition-all duration-300 ${open ? 'w-64' : 'w-0 overflow-hidden opacity-0'} shrink-0 h-full`}>
      <div className="h-16 flex items-center px-6 border-b border-slate-200 dark:border-gray-700 shrink-0">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center mr-3 shrink-0 shadow-sm" style={{ background: 'linear-gradient(135deg, var(--color-brand-400), var(--color-brand-700))' }}>
          <svg viewBox="0 0 24 24" fill="none" className="w-4.5 h-4.5">
            <path d="M6 17 C10 17 10 7 18 7" stroke="white" strokeWidth="2" strokeLinecap="round" />
            <circle cx="6" cy="17" r="2.5" fill="white" />
            <circle cx="18" cy="7" r="2.5" fill="white" fillOpacity="0.6" />
          </svg>
        </div>
        <div className="flex flex-col whitespace-nowrap">
          <span className="font-display font-bold text-slate-900 dark:text-white leading-tight">OpsAssist AI</span>
          <span className="text-[10px] text-slate-500 dark:text-gray-400 font-medium uppercase tracking-wider">Operations Console</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-4 px-3 flex flex-col gap-1 scrollbar-thin">
        {visibleItems.map((item, i) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.id}
              to={item.path}
              style={{ animation: `fade-in-up 0.4s var(--ease-out-expo) both`, animationDelay: `${i * 35}ms` }}
              className={({ isActive }) => `nav-link whitespace-nowrap ${isActive ? 'nav-link-active' : ''}`}
            >
              <Icon size={18} className="shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.id === 'escalations' && pendingEscalations > 0 && (
                <Badge variant="danger" className="shrink-0">{pendingEscalations}</Badge>
              )}
            </NavLink>
          );
        })}
      </div>

      <div className="p-4 border-t border-slate-200 dark:border-gray-700 shrink-0 whitespace-nowrap overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <Avatar name={agent.full_name} size="md" />
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-slate-900 dark:text-white truncate">{agent.full_name}</div>
            <div className="text-xs text-slate-500 dark:text-gray-400 truncate">{agent.role_label}</div>
          </div>
        </div>
        <button onClick={logout} className="btn btn-ghost w-full justify-start text-danger-600 hover:text-danger-700 hover:bg-danger-50 dark:hover:bg-red-900/20">
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
