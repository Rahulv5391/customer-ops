import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { ChatPanel } from '../chat/ChatPanel';
import { analyticsApi } from '../../api/analytics';
import { useAuth } from '../../hooks/useAuth';

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const { agent } = useAuth();

  useEffect(() => {
    if (agent?.role === 'team_lead') {
      analyticsApi.escalationsPending()
        .then(res => setPendingCount(res.count))
        .catch(() => {});
    }
  }, [agent]);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-gray-900">
      <Sidebar open={sidebarOpen} pendingEscalations={pendingCount} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <Topbar onToggle={() => setSidebarOpen(v => !v)} sidebarOpen={sidebarOpen} pendingEscalations={pendingCount} />
        <main className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-6 relative">
          <Outlet />
        </main>
      </div>
      <ChatPanel />
    </div>
  );
}
