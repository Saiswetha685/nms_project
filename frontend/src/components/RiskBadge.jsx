import React from 'react';

export default function RiskBadge({ level, score = null, size = 'md' }) {
  const norm = (level || 'LOW').toUpperCase();

  const configs = {
    LOW: {
      bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      label: 'LOW'
    },
    MEDIUM: {
      bg: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      label: 'MEDIUM'
    },
    HIGH: {
      bg: 'bg-amber-500/15 text-amber-400 border-amber-500/40',
      label: 'HIGH'
    },
    CRITICAL: {
      bg: 'bg-rose-500/20 text-rose-300 border-rose-500/50 shadow-sm shadow-rose-950/40',
      label: 'CRITICAL'
    }
  };

  const current = configs[norm] || configs.LOW;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 font-mono font-medium rounded-md border ${current.bg} ${padding}`}>
      <span className="font-sans font-bold">{current.label}</span>
      {score !== null && <span className="opacity-75">({score})</span>}
    </span>
  );
}
