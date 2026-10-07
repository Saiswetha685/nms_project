import React from 'react';
import {
  LayoutDashboard,
  Server,
  AlertTriangle,
  Bell,
  ShieldCheck,
  Cpu,
  FileText,
  PlayCircle,
  Settings
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'services', label: 'Services Registry', icon: Server },
  { id: 'incidents', label: 'NOC Incidents', icon: AlertTriangle },
  { id: 'alerts', label: 'Alert Stream', icon: Bell },
  { id: 'sla', label: 'SLA Compliance', icon: ShieldCheck },
  { id: 'ml', label: 'ML & Risk Intelligence', icon: Cpu },
  { id: 'reports', label: 'Audit Reports', icon: FileText },
  { id: 'simulation', label: 'Scenario Simulation', icon: PlayCircle },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ activeTab, onSelect, badgeCounts = {} }) {
  return (
    <aside className="w-64 border-r border-gray-800 bg-gray-950/70 backdrop-blur-md flex flex-col justify-between p-3 select-none">
      <nav className="space-y-1">
        <div className="px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-gray-500 font-mono">
          Operations & Analytics
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          const badge = badgeCounts[item.id];

          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 font-semibold shadow-sm'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-900 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-indigo-400' : 'text-gray-400 group-hover:text-gray-300'
                  }`}
                />
                <span>{item.label}</span>
              </div>

              {badge > 0 && (
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    item.id === 'incidents'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}
                >
                  {badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status info box */}
      <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-800/80 text-[11px] text-gray-400">
        <div className="flex items-center justify-between mb-1">
          <span className="font-semibold text-gray-300">NMS Core Engine</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-dot" />
        </div>
        <p className="text-[10px] text-gray-500 font-mono">Autonomous Polling: 20s</p>
        <p className="text-[10px] text-gray-500 font-mono">Decision: Deterministic Rule</p>
      </div>
    </aside>
  );
}
