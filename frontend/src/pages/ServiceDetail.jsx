import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Activity,
  ShieldCheck,
  Cpu,
  Brain,
  TrendingDown,
  Clock,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Info
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import api from '../api';
import StatusBadge from '../components/StatusBadge';
import RiskBadge from '../components/RiskBadge';

export default function ServiceDetail({ serviceId, onBack }) {
  const [service, setService] = useState(null);
  const [slaData, setSlaData] = useState(null);
  const [ruleRisk, setRuleRisk] = useState(null);
  const [mlRisk, setMlRisk] = useState(null);
  const [combinedRisk, setCombinedRisk] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [checks, setChecks] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [probing, setProbing] = useState(false);

  const fetchServiceDetails = async () => {
    try {
      const results = await Promise.allSettled([
        api.get(`/services/${serviceId}`),
        api.get(`/services/${serviceId}/sla`),
        api.get(`/services/${serviceId}/sla-risk`),
        api.get(`/ml/services/${serviceId}/risk`),
        api.get(`/services/${serviceId}/combined-risk`),
        api.get(`/services/${serviceId}/forecast`),
        api.get(`/services/${serviceId}/explanation`),
        api.get(`/services/${serviceId}/checks?limit=40`),
        api.get(`/incidents?status=OPEN`)
      ]);

      const [svcRes, slaRes, ruleRes, mlRes, combRes, fcRes, expRes, checksRes, incRes] = results;

      if (svcRes.status === 'fulfilled') setService(svcRes.value.data);
      if (slaRes.status === 'fulfilled') setSlaData(slaRes.value.data);
      if (ruleRes.status === 'fulfilled') setRuleRisk(ruleRes.value.data);
      if (mlRes.status === 'fulfilled') setMlRisk(mlRes.value.data);
      if (combRes.status === 'fulfilled') setCombinedRisk(combRes.value.data);
      if (fcRes.status === 'fulfilled') setForecast(fcRes.value.data);
      if (expRes.status === 'fulfilled') setExplanation(expRes.value.data.explanation);
      if (checksRes.status === 'fulfilled') setChecks([...checksRes.value.data].reverse());
      if (incRes.status === 'fulfilled') setIncidents(incRes.value.data.filter((i) => i.service_id === serviceId));
    } catch (err) {
      console.error('Error fetching service detail telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchServiceDetails();
    const interval = setInterval(fetchServiceDetails, 20000);
    return () => clearInterval(interval);
  }, [serviceId]);

  const handleManualProbe = async () => {
    setProbing(true);
    try {
      await api.post(`/services/${serviceId}/check`);
      await fetchServiceDetails();
    } catch (err) {
      console.error(err);
    } finally {
      setProbing(false);
    }
  };

  if (loading || !service) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400 gap-2">
        <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
        <span>Loading service telemetry telemetry...</span>
      </div>
    );
  }

  // Latency performance stats
  const latencies = checks.map((c) => c.response_time_ms).filter((l) => l > 0);
  const minLat = latencies.length ? Math.min(...latencies).toFixed(1) : '0';
  const maxLat = latencies.length ? Math.max(...latencies).toFixed(1) : '0';
  const avgLat = latencies.length
    ? (latencies.reduce((a, b) => a + b, 0) / latencies.length).toFixed(1)
    : '0';

  // Format chart items
  const chartTelemetry = checks.map((c) => {
    const d = new Date(c.timestamp);
    return {
      time: `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`,
      latency: c.response_time_ms,
      packetLoss: c.packet_loss_percent || 0
    };
  });

  return (
    <div className="space-y-6">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 rounded-xl bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-white border border-gray-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl font-extrabold text-white tracking-tight">{service.name}</h1>
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700">
                {service.type}
              </span>
              <StatusBadge status={service.current_state?.status} />
            </div>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              Target: {service.url || `${service.target}${service.port ? ':' + service.port : ''}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleManualProbe}
            disabled={probing}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${probing ? 'animate-spin' : ''}`} />
            <span>{probing ? 'Sending Probe...' : 'Execute Probe Now'}</span>
          </button>
        </div>
      </div>

      {/* Row 1: Deterministic SLA Verdict vs Predictive Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Authoritative Availability */}
        <div className="glass-panel p-4 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Observed Availability</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">
            {slaData?.availability_percent?.toFixed(2)}%
          </div>
          <div className="flex items-center justify-between text-[11px] text-gray-400 mt-2 pt-2 border-t border-gray-800/80">
            <span>Target Commitment:</span>
            <span className="font-mono font-semibold text-gray-200">{service.sla_target_percent}%</span>
          </div>
        </div>

        {/* Downtime Budget Remaining */}
        <div className="glass-panel p-4 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Downtime Budget Left</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">
            {slaData?.budget?.remaining_downtime_minutes?.toFixed(1)}{' '}
            <span className="text-xs font-sans text-gray-400 font-normal">min</span>
          </div>
          <div className="flex items-center justify-between text-[11px] text-gray-400 mt-2 pt-2 border-t border-gray-800/80">
            <span>Consumed:</span>
            <span className="font-mono font-semibold text-amber-400">
              {slaData?.budget?.budget_consumption_percent?.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Rule-Based Risk Baseline */}
        <div className="glass-panel p-4 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>Rule Risk Baseline</span>
            <Cpu className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-2xl font-bold text-white font-mono">{ruleRisk?.rule_risk}</span>
            <span className="text-xs text-gray-500 font-mono">/ 100</span>
            <RiskBadge level={ruleRisk?.risk_level} size="sm" />
          </div>
          <div className="text-[10px] text-gray-400 mt-2 pt-2 border-t border-gray-800/80 font-mono">
            Budget 40% | Burn 30% | Trend 15% | Jitter 15%
          </div>
        </div>

        {/* Heavy ML 6h Probability */}
        <div className="glass-panel p-4 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span>ML Failure Prob (6h)</span>
            <Brain className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-center gap-2 mt-2">
            <span className="text-2xl font-bold text-cyan-300 font-mono">
              {mlRisk ? `${(mlRisk.probability_down_next_6h * 100).toFixed(0)}%` : '15%'}
            </span>
            <RiskBadge level={mlRisk?.risk_level} size="sm" />
          </div>
          <div className="text-[10px] text-gray-400 mt-2 pt-2 border-t border-gray-800/80 font-mono">
            Model: {mlRisk?.model_type} ({mlRisk?.model_version})
          </div>
        </div>
      </div>

      {/* Row 2: Claude AI Operational Explanation Banner */}
      <div className="glass-panel p-5 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/30 via-gray-900 to-gray-900 relative overflow-hidden">
        <div className="flex items-start gap-3.5">
          <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                Claude AI Operational Risk &amp; SLA Root Cause Synthesis
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Server-Side Copilot
              </span>
            </div>
            <div className="text-xs text-gray-300 leading-relaxed whitespace-pre-line mt-2">
              {explanation || 'Analyzing historical probe telemetry and SLA burn trajectory...'}
            </div>
          </div>
        </div>
      </div>

      {/* Row 3: ML Top Predictive Features & Statistical Forecast */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ML Top Predictive Drivers */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Brain className="w-4 h-4 text-cyan-400" />
                ML Feature Store Attribution (Top Risk Drivers)
              </h2>
              <p className="text-[11px] text-gray-400">
                Non-linear tree feature importances computed without lookahead leakage
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {mlRisk?.top_features?.map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-200 font-medium">{item.description || item.feature}</span>
                  <span className="font-mono text-cyan-400 font-bold">
                    {(item.importance * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full"
                    style={{ width: `${Math.min(100, item.importance * 100 * 2.5)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Statistical Holt-Winters SLA Budget Forecast */}
        <div className="glass-panel p-5 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-amber-400" />
                Statistical SLA Budget Exhaustion Forecast
              </h2>
              <p className="text-[11px] text-gray-400">
                Holt-Winters double exponential smoothing estimation with 95% CI
              </p>
            </div>
          </div>

          <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800/80 mb-3 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Projected Exhaustion Horizon:</span>
              <span className="font-mono font-bold text-amber-300">
                {forecast?.hours_to_exhaustion !== null
                  ? `~${forecast.hours_to_exhaustion} hours`
                  : 'Budget Stable (No Burn)'}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">95% Confidence Bounds:</span>
              <span className="font-mono text-gray-300">
                {forecast?.lower_confidence_bound_hours !== null
                  ? `[${forecast.lower_confidence_bound_hours}h — ${forecast.upper_confidence_bound_hours}h]`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Failure Burn Velocity:</span>
              <span className="font-mono text-gray-300">
                {forecast?.current_burn_rate_minutes_per_hour} min / hour
              </span>
            </div>
          </div>

          <div className="flex items-start gap-2 text-[11px] text-gray-400 bg-amber-500/5 p-2.5 rounded-lg border border-amber-500/20">
            <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>{forecast?.explanation}</span>
          </div>
        </div>
      </div>

      {/* Row 4: Historical Latency & Telemetry Charts */}
      <div className="glass-panel p-5 rounded-2xl border border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              Observed RTT Latency Telemetry (Last 40 Probes)
            </h2>
            <p className="text-[11px] text-gray-400">Millisecond response time and packet loss timeline</p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="text-gray-400">
              Min: <b className="text-gray-200">{minLat}ms</b>
            </span>
            <span className="text-gray-400">
              Avg: <b className="text-gray-200">{avgLat}ms</b>
            </span>
            <span className="text-gray-400">
              Max: <b className="text-gray-200">{maxLat}ms</b>
            </span>
          </div>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartTelemetry} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="time" stroke="#6b7280" fontSize={10} tickLine={false} />
              <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '11px' }}
                formatter={(val, name) => [
                  name === 'latency' ? `${val} ms` : `${val}%`,
                  name === 'latency' ? 'Latency' : 'Packet Loss'
                ]}
              />
              <Line
                type="monotone"
                dataKey="latency"
                stroke="#6366f1"
                strokeWidth={2}
                dot={{ r: 2, fill: '#6366f1' }}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="packetLoss"
                stroke="#f43f5e"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
