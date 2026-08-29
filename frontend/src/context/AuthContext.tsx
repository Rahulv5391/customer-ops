import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { authApi } from '../api/auth';
import type { AgentResponse } from '../types';

interface AuthContextValue {
  agent: AgentResponse | null;
  isLoggedIn: boolean;
  isLoading: boolean;
  login(agent: AgentResponse, token: string): void;
  logout(): void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [agent, setAgent] = useState<AgentResponse | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('ops_token');
    if (!token) { setIsLoading(false); return; }
    authApi.me()
      .then(data => { setAgent(data); setIsLoggedIn(true); })
      .catch(() => { localStorage.removeItem('ops_token'); })
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback((agentData: AgentResponse, token: string) => {
    localStorage.setItem('ops_token', token);
    setAgent(agentData);
    setIsLoggedIn(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('ops_token');
    setAgent(null);
    setIsLoggedIn(false);
  }, []);

  return (
    <AuthContext.Provider value={{ agent, isLoggedIn, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
