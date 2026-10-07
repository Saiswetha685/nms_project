import React, { useState, useEffect } from 'react';
import {
  PlayCircle,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Flame,
  XCircle,
  RotateCcw,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import api from '../api';
import { useWebSocket } from '../context/WebSocketContext';
import StatusBadge from '../components/StatusBadge';

const STAGES = [
  {
    stage: 1,
    title: 'Stage 1: Normal Baseline',
    desc: 'Low latency (~45ms), 0% packet loss, nominal SLA compliance.',
    icon: CheckCircle2,
    color: 'text-emerald-400',
    border: 'border-emerald-500/30'
  },
  {
    stage: 2,
    title: 'Stage 2: Latency Degradation',
    desc: 'Response time escalates (~380ms), warning status triggered.',
    icon: AlertTriangle,
    color: 'text-amber-400',
    border: 'border-amber-500/30'
  },
  {
    stage: 3,
    title: 'Stage 3: Packet Loss & Jitter',
    desc: 'Critical jitter, packet loss (~20%), failure velocity surges.',
    icon: Flame,
    color: 'text-orange-400',
    border: 'border-orange-500/30'
  },
  {
    stage: 4,
    title: 'Stage 4: High SLA Risk Warning',
    desc: 'ML failure probability escalates to 82%, proactive early alert sent!',
    icon: Sparkles,
    color: 'text-cyan-400',
    border: 'border-cyan-500/30'
  },
  {
    stage: 5,
    title: 'Stage 5: Outage & SLA Violation',
    desc: 'Confirmed DOWN, consecutive check failures, NOC incident created.',
    icon: XCircle,
    color: 'text-rose-400',
    border: 'border-rose-500/30'
  },
  {
    stage: 6,
    title: 'Stage 6: Restitution & Recovery',
    desc: 'Anti-flapping confirms recovery, incident resolved, MTTR recorded.',
    icon: RotateCcw,
    color: 'text-indigo-400',
    border: 'border-indigo-500/30'
  }
];

export default function Simulation({ onSelectService }) {
  const [currentStage, setCurrentStage] = useState(1);
  const [selectedServiceId, setSelectedServiceId] = useState('svc_student_portal');
  const [services, setServices] = useState([]);
  const [lastStageResult, setLastStageResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    async function init() {
      try {
        const [statusRes, svcRes] = await Promise.all([
          api.get('/demo/status'),
          api.get('/services')
        ]);
        setCurrentStage(statusRes.data.current_stage || 1);
        setServices(svcRes.data);
      } catch (err) {
        console.error(err);
      }
    }
    init();

    const unsub = subscribe('simulation_stage_changed', (data) => {
      setCurrentStage(data.stage);
      setLastStageResult(data);
    });

    return () => unsub();
  }, []);

  const handleTriggerStage = async (stageNumber) => {
    setSubmitting(true);
    try {
      const res = await api.post(`/demo/sla-risk/stage/${stageNumber}?service_id=${selectedServiceId}`);
      setCurrentStage(stageNumber);
      setLastStageResult(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to trigger simulation stage');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <PlayCircle className="w-5 h-5 text-indigo-400" />
            <span>Interactive Multi-Stage SLA Risk Simulation</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Demonstrates deterministic health evaluation, ML proactive warning, outage, and recovery in live real-time
          </p>
        </div>

        {/* Target Service Selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">Target Service:</label>
          <select
            value={selectedServiceId}
            onChange={(e) => setSelectedServiceId(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white"
          >
            {services.map((s) => (
              <option key={s.service_id} value={s.service_id}>
                {s.name} ({s.type})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Progressive Stage Stepper */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {STAGES.map((st) => {
          const Icon = st.icon;
          const isCurrent = currentStage === st.stage;

          return (
            <div
              key={st.stage}
              className={`glass-panel p-4 rounded-xl border transition-all flex flex-col justify-between ${
                isCurrent
                  ? `${st.border} bg-indigo-950/20 shadow-lg shadow-indigo-950/40 ring-1 ring-indigo-500/40`
                  : 'border-gray-800/80 hover:border-gray-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-gray-950 text-gray-400 border border-gray-800">
                    STAGE {st.stage}
                  </span>
                  <Icon className={`w-4 h-4 ${st.color}`} />
                </div>

                <h3 className="text-xs font-bold text-white mb-1">{st.title}</h3>
                <p className="text-[11px] text-gray-400 leading-relaxed">{st.desc}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-800/80 flex items-center justify-between">
                {isCurrent ? (
                  <span className="text-[10px] font-mono font-bold text-cyan-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                    CURRENT STATE
                  </span>
                ) : (
                  <span className="text-[10px] text-gray-500 font-mono">Idle</span>
                )}

                <button
                  onClick={() => handleTriggerStage(st.stage)}
                  disabled={submitting}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'bg-gray-800 hover:bg-gray-700 text-gray-200'
                  }`}
                >
                  <span>Inject Stage</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Simulation Feedback Console */}
      <div className="glass-panel p-5 rounded-2xl border border-gray-800">
        <h2 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
          <Activity className="w-4 h-4 text-cyan-400" />
          Live Telemetry Simulation Telemetry Feed
        </h2>

        {lastStageResult ? (
          <div className="bg-gray-950/70 p-4 rounded-xl border border-gray-800/80 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">{lastStageResult.stage_name}</span>
              <StatusBadge status={lastStageResult.status} />
            </div>

            <p className="text-gray-300 font-sans">{lastStageResult.narrative || lastStageResult.message}</p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-gray-800 text-[11px] font-mono text-gray-400">
              <div>
                Latency: <b className="text-white">{lastStageResult.response_time_ms} ms</b>
              </div>
              <div>
                Packet Loss: <b className="text-white">{lastStageResult.packet_loss_percent}%</b>
              </div>
              <div>
                Target Service: <b className="text-indigo-300">{lastStageResult.service_name}</b>
              </div>
              <div>
                Timestamp: <b className="text-gray-300">{new Date(lastStageResult.timestamp).toLocaleTimeString()}</b>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500 text-xs py-4 text-center font-mono">
            Click any stage above to inject simulated anomalies and watch the dashboard update live via WebSockets.
          </div>
        )}
      </div>
    </div>
  );
}
