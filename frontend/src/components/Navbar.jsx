import React from 'react';
import { Activity, Radio, PlayCircle, LogOut, ShieldCheck, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';

export default function Navbar({ onNavigate, activeTab }) {
  const { user, logout, isAdmin } = useAuth();
  const { connected } = useWebSocket();

  return (
    <header className="h-16 border-b border-gray-800 bg-gray-900/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-extrabold text-base tracking-tight text-white">SLA-Predict</span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 uppercase tracking-wider">
              NMS AI
            </span>
          </div>
          <p className="text-[11px] text-gray-400 font-mono -mt-0.5">Predictive Service SLA Telemetry</p>
        </div>
      </div>

      {/* Middle Status & Quick Controls */}
      <div className="hidden md:flex items-center gap-4">
        {/* Live WS Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-950/60 border border-gray-800 text-xs">
          <Radio className={`w-3.5 h-3.5 ${connected ? 'text-emerald-400 animate-pulse' : 'text-amber-400'}`} />
          <span className="text-gray-300 font-mono text-[11px]">
            {connected ? 'Telemetry Stream: Active' : 'Connecting Stream...'}
          </span>
        </div>

        {/* Quick Demo Simulator CTA */}
        <button
          onClick={() => onNavigate('simulation')}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
            activeTab === 'simulation'
              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
              : 'bg-gray-800/80 text-gray-200 border-gray-700 hover:bg-gray-700/80 hover:text-white'
          }`}
        >
          <PlayCircle className="w-3.5 h-3.5 text-cyan-400" />
          <span>Interactive Simulation</span>
        </button>
      </div>

      {/* User profile & Logout */}
      <div className="flex items-center gap-3">
        {user && (
          <div className="flex items-center gap-3 pl-3 border-l border-gray-800">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-gray-200 flex items-center gap-1.5 justify-end">
                <span>{user.name}</span>
                {isAdmin ? (
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                ) : (
                  <User className="w-3.5 h-3.5 text-emerald-400" />
                )}
              </div>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-gray-800 text-gray-400">
                {user.role}
              </span>
            </div>

            <button
              onClick={logout}
              title="Sign out"
              className="p-2 rounded-lg text-gray-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
