import { Menu, Sun, Moon, Bell, ChevronDown } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useTheme } from '../../hooks/useTheme';
import { useAuth } from '../../hooks/useAuth';
import { Avatar } from '../ui';

interface TopbarProps {
  onToggle(): void;
  sidebarOpen: boolean;
  pendingEscalations: number;
}

const routeNames: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/customers': 'Customers',
  '/tickets': 'Ticket Queue',
  '/knowledge-base': 'Knowledge Base',
  '/directory': 'Agent Directory',
  '/escalations': 'Escalations',
  '/data-sources': 'Data Sources',
  '/activity-log': 'Activity Log',
};

export function Topbar({ onToggle, pendingEscalations }: TopbarProps) {
  const { theme, toggleTheme } = useTheme();
  const { agent } = useAuth();
  const location = useLocation();

  const title = routeNames[location.pathname] || 'OpsAssist AI';

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-slate-200 dark:border-gray-700 flex items-center justify-between px-4 shrink-0">
      <div className="flex items-center gap-4">
        <button onClick={onToggle} className="p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-gray-700 transition">
          <Menu size={20} />
        </button>
        <h1 className="text-lg font-semibold text-slate-900 dark:text-white">{title}</h1>
      </div>

      <div className="flex items-center gap-3">
        <button onClick={toggleTheme} className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-gray-700 transition">
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>

        <div className="relative">
          <button className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-gray-700 transition">
            <Bell size={20} />
            {pendingEscalations > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-danger-500 rounded-full border-2 border-white dark:border-gray-800" />
            )}
          </button>
        </div>

        <div className="h-6 w-px bg-slate-200 dark:bg-gray-700 mx-1" />

        <div className="flex items-center gap-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-gray-700 py-1 px-2 rounded-lg transition">
          <Avatar name={agent?.full_name || 'Agent'} size="sm" />
          <ChevronDown size={14} className="text-slate-400" />
        </div>
      </div>
    </header>
  );
}
