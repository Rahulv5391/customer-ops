import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ToastContainer, Spinner } from './components/ui';
import { Layout } from './components/layout/Layout';

import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Customers } from './pages/Customers';
import { CustomerDetail } from './pages/CustomerDetail';
import { TicketQueue } from './pages/TicketQueue';
import { TicketDetail } from './pages/TicketDetail';
import { Escalations } from './pages/Escalations';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { Directory } from './pages/Directory';
import { DataSources } from './pages/DataSources';
import { ActivityLog } from './pages/ActivityLog';

function PrivateRoute() {
  const { isLoggedIn } = useAuth();
  return isLoggedIn ? <Outlet /> : <Navigate to="/login" replace />;
}

function TeamLeadRoute() {
  const { agent } = useAuth();
  return agent?.role === 'team_lead' ? <Outlet /> : <Navigate to="/dashboard" replace />;
}

function AppRoutes() {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-50 dark:bg-gray-900">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route element={<PrivateRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/customers/:id" element={<CustomerDetail />} />
          <Route path="/tickets" element={<TicketQueue />} />
          <Route path="/tickets/:id" element={<TicketDetail />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />
          <Route path="/directory" element={<Directory />} />
          
          <Route element={<TeamLeadRoute />}>
            <Route path="/escalations" element={<Escalations />} />
            <Route path="/data-sources" element={<DataSources />} />
            <Route path="/activity-log" element={<ActivityLog />} />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
            <ToastContainer />
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </ThemeProvider>
  );
}
