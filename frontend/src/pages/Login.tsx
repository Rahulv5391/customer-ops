import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Input, Button } from '../components/ui';
import { Inbox, ShieldCheck, Sparkles } from 'lucide-react';

const highlights = [
  { icon: Sparkles, label: 'AI Agent Assist', detail: 'Grounded, source-cited answers on every reply' },
  { icon: Inbox, label: 'Unified Queue', detail: 'Email, chat, phone & social in one board' },
  { icon: ShieldCheck, label: 'Escalation Guardrails', detail: 'Nothing writes to a record without review' },
];

export function Login() {
  const [email, setEmail] = useState('jordan.lee@customerops.demo');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const { authApi } = await import('../api/auth');
      const res = await authApi.login(email, password);
      login(res.agent, res.access_token);
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-gray-900">
      {/* Left: brand / value panel */}
      <div
        className="hidden lg:flex lg:w-[46%] relative flex-col justify-between p-12 overflow-hidden text-white"
        style={{ background: 'linear-gradient(155deg, var(--color-brand-800) 0%, var(--color-brand-900) 55%, var(--color-slate-950) 100%)' }}
      >
        {/* decorative grid + glow */}
        <div
          className="absolute inset-0 opacity-[0.12]"
          style={{ backgroundImage: 'linear-gradient(white 1px, transparent 1px), linear-gradient(90deg, white 1px, transparent 1px)', backgroundSize: '42px 42px' }}
        />
        <div className="absolute -top-24 -right-16 w-80 h-80 rounded-full bg-brand-400/30 blur-3xl animate-float-slow" />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full bg-brand-300/10 blur-3xl animate-float-slow" style={{ animationDelay: '1.5s' }} />

        <div className="relative z-10 animate-fade-in-up">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-8 shadow-lg" style={{ background: 'linear-gradient(135deg, var(--color-brand-300), var(--color-brand-500))' }}>
            <svg viewBox="0 0 24 24" fill="none" className="w-5.5 h-5.5">
              <path d="M6 17 C10 17 10 7 18 7" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <circle cx="6" cy="17" r="2.5" fill="white" />
              <circle cx="18" cy="7" r="2.5" fill="white" fillOpacity="0.6" />
            </svg>
          </div>
          <h1 className="font-display text-4xl font-bold leading-tight max-w-sm">
            Every ticket, resolved with a paper trail.
          </h1>
          <p className="text-brand-100/80 mt-4 max-w-sm text-[15px] leading-relaxed">
            One console for your queues, your customer records, and an assistant that cites its source before it touches either.
          </p>
        </div>

        <div className="relative z-10 flex flex-col gap-3">
          {highlights.map((h, i) => {
            const Icon = h.icon;
            return (
              <div
                key={h.label}
                className="flex items-center gap-3 bg-white/10 backdrop-blur-sm border border-white/10 rounded-xl px-4 py-3 animate-fade-in-up"
                style={{ animationDelay: `${150 + i * 90}ms` }}
              >
                <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
                  <Icon size={16} className="text-brand-200" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold leading-tight">{h.label}</div>
                  <div className="text-xs text-brand-100/70 leading-tight mt-0.5">{h.detail}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: form panel */}
      <div className="flex-1 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm animate-fade-in-up">
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm" style={{ background: 'linear-gradient(135deg, var(--color-brand-400), var(--color-brand-700))' }}>
              <svg viewBox="0 0 24 24" fill="none" className="w-5 h-5">
                <path d="M6 17 C10 17 10 7 18 7" stroke="white" strokeWidth="2" strokeLinecap="round" />
                <circle cx="6" cy="17" r="2.5" fill="white" />
                <circle cx="18" cy="7" r="2.5" fill="white" fillOpacity="0.6" />
              </svg>
            </div>
            <span className="font-display font-bold text-xl text-slate-900 dark:text-white">OpsAssist AI</span>
          </div>

          <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Welcome back</h2>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1.5 mb-8">Sign in to your operations console.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5">
            {error && (
              <div className="p-3 bg-red-50 text-red-600 border border-red-100 rounded-lg text-sm font-medium animate-fade-in-up dark:bg-red-900/20 dark:border-red-900/40 dark:text-red-400">
                {error}
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="agent@customerops.demo"
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
            />

            <Button type="submit" loading={loading} className="w-full mt-2 py-2.5 text-base">
              Sign in
            </Button>
          </form>

          <p className="text-xs text-slate-400 dark:text-gray-500 text-center mt-8">
            Demo credentials are pre-filled — just sign in.
          </p>
        </div>
      </div>
    </div>
  );
}
