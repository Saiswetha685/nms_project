import React, { useState } from 'react';
import { Activity, ShieldCheck, UserCheck, Lock, Mail, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoFill = (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#0B0F19] relative overflow-hidden">
      {/* Decorative gradient glow blobs */}
      <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-96 h-96 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full glass-panel rounded-2xl p-8 shadow-2xl relative z-10 border border-gray-800">
        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-xl shadow-indigo-600/25 mb-4">
            <Activity className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">SLA-Predict NOC</h1>
          <p className="text-xs text-gray-400 mt-1">
            Intelligent Network Service Monitoring & Predictive SLA Violation Detection
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@slapredict.io"
                className="w-full bg-gray-950/70 border border-gray-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-gray-950/70 border border-gray-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full mt-2 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white font-semibold py-2.5 px-4 rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/30 transition-all cursor-pointer disabled:opacity-50"
          >
            <span>{submitting ? 'Authenticating...' : 'Sign In to Operations Console'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Fast Login Pills */}
        <div className="mt-8 pt-6 border-t border-gray-800">
          <div className="text-[11px] font-mono text-gray-400 text-center mb-3">
            Quick College Demo Credentials
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleDemoFill('admin@slapredict.io', 'Admin@123')}
              className="flex items-center gap-2 p-2 rounded-lg bg-gray-950/60 border border-gray-800 hover:border-indigo-500/50 text-left transition-all group cursor-pointer"
            >
              <ShieldCheck className="w-4 h-4 text-indigo-400 group-hover:scale-110 transition-transform" />
              <div>
                <div className="text-[11px] font-semibold text-gray-200">Admin Account</div>
                <div className="text-[10px] text-gray-500 font-mono">Full Control</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleDemoFill('operator@slapredict.io', 'Operator@123')}
              className="flex items-center gap-2 p-2 rounded-lg bg-gray-950/60 border border-gray-800 hover:border-cyan-500/50 text-left transition-all group cursor-pointer"
            >
              <UserCheck className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
              <div>
                <div className="text-[11px] font-semibold text-gray-200">Operator</div>
                <div className="text-[10px] text-gray-500 font-mono">Read & Ack</div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
