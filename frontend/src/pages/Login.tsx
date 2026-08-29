import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Input, Button } from '../components/ui';

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
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-800 to-indigo-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl overflow-hidden">
        <div className="p-8 pb-6 border-b border-slate-100 flex flex-col items-center">
          <div className="w-12 h-12 bg-brand-600 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-brand-500/30">
            <span className="text-white font-bold text-2xl leading-none">O</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">OpsAssist AI</h1>
          <p className="text-sm text-slate-500 mt-1">Operations Console Sign In</p>
        </div>

        <form onSubmit={handleSubmit} className="p-8 flex flex-col gap-5">
          {error && (
            <div className="p-3 bg-red-50 text-red-600 border border-red-100 rounded-lg text-sm font-medium">
              {error}
            </div>
          )}
          
          <Input 
            label="Email Address" 
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
            Sign In
          </Button>
        </form>
      </div>
    </div>
  );
}
