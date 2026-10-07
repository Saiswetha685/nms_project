import React from 'react';

export default function StatusBadge({ status, showDot = true, size = 'md' }) {
  const norm = (status || 'UNKNOWN').toUpperCase();

  const configs = {
    HEALTHY: {
      bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      dot: 'bg-emerald-400',
      label: 'HEALTHY'
    },
    WARNING: {
      bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      dot: 'bg-amber-400',
      label: 'WARNING'
    },
    CRITICAL: {
      bg: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
      dot: 'bg-orange-400',
      label: 'CRITICAL'
    },
    DOWN: {
      bg: 'bg-rose-500/15 text-rose-400 border-rose-500/40 shadow-sm shadow-rose-900/30',
      dot: 'bg-rose-500 animate-pulse',
      label: 'DOWN'
    },
    UNKNOWN: {
      bg: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
      dot: 'bg-slate-400',
      label: 'UNKNOWN'
    }
  };

  const current = configs[norm] || configs.UNKNOWN;
  const padding = size === 'sm' ? 'px-2 py-0.5 text-xs' : size === 'lg' ? 'px-3.5 py-1.5 text-sm' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 font-semibold rounded-full border ${current.bg} ${padding} tracking-wide transition-colors`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${current.dot}`} />}
      {current.label}
    </span>
  );
}
