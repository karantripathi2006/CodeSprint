import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Brain, Lock, User } from 'lucide-react';
import { useState } from 'react';
import { setToken } from '../utils/api';

export default function Login() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('password');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // OAuth2 password flow — backend expects form-encoded body
      const body = new URLSearchParams({ username, password });
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Invalid credentials');
      }

      const data = await res.json();
      setToken(data.access_token);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[color:var(--bg-primary)] p-4 relative overflow-hidden">
      {/* Background Decorative Elements */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-indigo-600/20 blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-purple-600/20 blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="glass-panel rounded-2xl p-8 shadow-2xl">
          <div className="mb-8 flex flex-col items-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-indigo-500/30">
              <Brain size={32} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">HR Login</h1>
            <p className="mt-2 text-sm text-slate-400">Access the ResuMatch Platform</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            <div className="space-y-4">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User size={18} className="text-slate-400" />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-[#2a3050] rounded-xl leading-5 bg-[#0f1525] text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors"
                  placeholder="Username"
                />
              </div>

              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock size={18} className="text-slate-400" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-[#2a3050] rounded-xl leading-5 bg-[#0f1525] text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition-colors"
                  placeholder="Password"
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-400 text-center bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-xl text-white bg-gradient-primary hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-[#0a0e1a] shadow-lg shadow-indigo-500/25 transition-all disabled:opacity-50"
            >
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                <Lock className="h-5 w-5 text-white/50 group-hover:text-white/80 transition-colors" />
              </span>
              {loading ? 'Authenticating...' : 'Sign in'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <a href="#" className="text-sm font-medium text-indigo-400 hover:text-indigo-300 transition-colors">
              Forgot your password?
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
