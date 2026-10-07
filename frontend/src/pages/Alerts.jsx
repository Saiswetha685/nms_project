import React, { useState, useEffect } from 'react';
import { Bell, CheckCircle, AlertOctagon, Info, RefreshCw, Check } from 'lucide-react';
import api from '../api';
import { useWebSocket } from '../context/WebSocketContext';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [unackOnly, setUnackOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const { subscribe } = useWebSocket();

  const loadAlerts = async () => {
    try {
      const res = await api.get(`/alerts?unack_only=${unackOnly}`);
      setAlerts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();

    const unsub = subscribe('simulation_stage_changed', () => {
      loadAlerts();
    });

    const interval = setInterval(loadAlerts, 15000);
    return () => {
      unsub();
      clearInterval(interval);
    };
  }, [unackOnly]);

  const handleAcknowledge = async (alertId) => {
    try {
      await api.post(`/alerts/${alertId}/acknowledge`);
      loadAlerts();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to acknowledge alert');
    }
  };

  const severityIcons = {
    CRITICAL: <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0" />,
    WARNING: <AlertOctagon className="w-4 h-4 text-amber-400 shrink-0" />,
    INFO: <Info className="w-4 h-4 text-cyan-400 shrink-0" />
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Bell className="w-5 h-5 text-amber-400" />
            <span>Alerts &amp; Proactive Notification Stream</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Event-driven deduplicated alerts for confirmed outages, high SLA risks, and ML failure warnings
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={unackOnly}
              onChange={(e) => setUnackOnly(e.target.checked)}
              className="rounded bg-gray-950 border-gray-700 text-indigo-600"
            />
            <span>Unacknowledged Only</span>
          </label>

          <button
            onClick={loadAlerts}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 text-xs font-medium"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Alerts Stream List */}
      <div className="space-y-3">
        {alerts.map((alt) => {
          const isCrit = alt.severity === 'CRITICAL';
          const isWarn = alt.severity === 'WARNING';

          return (
            <div
              key={alt.alert_id}
              className={`glass-panel p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all ${
                alt.acknowledged
                  ? 'border-gray-800/80 opacity-60'
                  : isCrit
                  ? 'border-rose-500/40 bg-rose-950/10'
                  : isWarn
                  ? 'border-amber-500/30 bg-amber-950/10'
                  : 'border-cyan-500/30 bg-cyan-950/10'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-gray-950/80 border border-gray-800 mt-0.5">
                  {severityIcons[alt.severity] || <Info className="w-4 h-4 text-gray-400" />}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white text-xs">
                      {alt.service_name || alt.service_id}
                    </span>
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                        isCrit
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                          : isWarn
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                          : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                      }`}
                    >
                      {alt.type}
                    </span>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {new Date(alt.created_at).toLocaleTimeString()}
                    </span>
                  </div>

                  <p className="text-xs text-gray-300 mt-1 font-sans">{alt.message}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                {alt.acknowledged ? (
                  <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Ack: {alt.acknowledged_by || 'Admin'}</span>
                  </span>
                ) : (
                  <button
                    onClick={() => handleAcknowledge(alt.alert_id)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-indigo-600 text-gray-200 hover:text-white border border-gray-700 text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Acknowledge</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}

        {alerts.length === 0 && (
          <div className="text-center py-12 glass-panel rounded-2xl border border-gray-800 text-gray-400 text-xs">
            No active alerts in stream. All service thresholds nominal.
          </div>
        )}
      </div>
    </div>
  );
}
