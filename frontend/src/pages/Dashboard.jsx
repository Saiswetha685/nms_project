import React, { useState, useEffect } from 'react';
import {
  Server,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  XCircle,
  ShieldAlert,
  Flame,
  LifeBuoy,
  RefreshCw,
  ArrowUpRight,
  TrendingUp,
  Activity
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import api from '../api';
import StatusBadge from '../components/StatusBadge';
import RiskBadge from '../components/RiskBadge';
import { useWebSocket } from '../context/WebSocketContext';

export default function Dashboard({ onSelectService, onNavigate }) {
  const [services, setServices] = useState([]);
  const [slaOverview, setSlaOverview] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { subscribe } = useWebSocket();

  const loadData = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const [svcRes, slaRes, incRes] = await Promise.all([
        api.get('/services'),
        api.get('/sla/overview'),
        api.get('/incidents?status=OPEN')
      ]);
      setServices(svcRes.data);
      setSlaOverview(slaRes.data);
      setIncidents(incRes.data);
    } catch (err) {
      console.error('Error fetching dashboard telemetry:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();

    // Subscribe to live websocket updates
    const unsub = subscribe('service_checked', (data) => {
      setServices((prev) =>
        prev.map((s) => {
          if (s.service_id === data.service_id) {
            return {
              ...s,
              current_state: {
                ...s.current_state,
                status: data.status,
                response_time_ms: data.response_time_ms,
                packet_loss_percent: data.packet_loss_percent,
                last_check: data.timestamp
              }
            };
          }
          return s;
        })
      );
    });

    const unsubSim = subscribe('simulation_stage_changed', () => {
      loadData();
    });

    const interval = setInterval(loadData, 20000);
    return () => {
      unsub();
      unsubSim();
      clearInterval(interval);
    };
  }, []);

  const total = services.length;
  const healthy = services.filter((s) => s.current_state?.status === 'HEALTHY').length;
  const warning = services.filter((s) => s.current_state?.status === 'WARNING').length;
  const critical = services.filter((s) => s.current_state?.status === 'CRITICAL').length;
  const down = services.filter((s) => s.current_state?.status === 'DOWN').length;

  const violations = slaOverview.filter((s) => s.compliance_state === 'VIOLATED').length;
  const atRisk = slaOverview.filter((s) => s.compliance_state === 'AT_RISK' || s.budget_consumption_percent >= 75).length;
  const openIncidents = incidents.length;

  // Chart telemetry data
  const chartData = services.map((s) => {
    const sla = slaOverview.find((o) => o.service_id === s.service_id);
    return {
      name: s.name.length > 14 ? s.name.slice(0, 14) + '...' : s.name,
      fullName: s.name,
      latency: s.current_state?.response_time_ms || 0,
      slaActual: sla?.actual_percent || 100,
      slaTarget: s.sla_target_percent,
      budgetUsed: sla?.budget_consumption_percent || 0,
      status: s.current_state?.status || 'HEALTHY'
    };
  });

  const triggerManualCheck = async (e, sid) => {
    e.stopPropagation();
    try {
      await api.post(`/services/${sid}/check`);
      loadData();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <span>Operations Telemetry Dashboard</span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Real-time deterministic availability, SLA compliance verification, and predictive ML short-term failure intelligence
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>{refreshing ? 'Syncing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      {/* 8 Primary KPI Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {/* Total Services */}
        <div className="glass-panel p-3.5 rounded-xl border border-gray-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-gray-400 text-xs">
            <span className="font-medium">Total</span>
            <Server className="w-4 h-4 text-gray-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2 font-mono">{total}</div>
          <div className="text-[10px] text-gray-500 mt-1">Targets Active</div>
        </div>

        {/* Healthy */}
        <div className="glass-panel p-3.5 rounded-xl border border-emerald-950/40 bg-emerald-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400 text-xs">
            <span className="font-medium">Healthy</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-300 mt-2 font-mono">{healthy}</div>
          <div className="text-[10px] text-emerald-500/70 mt-1">Passing Baseline</div>
        </div>

        {/* Warning */}
        <div className="glass-panel p-3.5 rounded-xl border border-amber-950/40 bg-amber-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-amber-400 text-xs">
            <span className="font-medium">Warning</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-2 font-mono">{warning}</div>
          <div className="text-[10px] text-amber-500/70 mt-1">Degraded RTT</div>
        </div>

        {/* Critical */}
        <div className="glass-panel p-3.5 rounded-xl border border-orange-950/40 bg-orange-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-orange-400 text-xs">
            <span className="font-medium">Critical</span>
            <AlertOctagon className="w-4 h-4 text-orange-400" />
          </div>
          <div className="text-2xl font-bold text-orange-300 mt-2 font-mono">{critical}</div>
          <div className="text-[10px] text-orange-500/70 mt-1">Near Outage</div>
        </div>

        {/* Down */}
        <div className="glass-panel p-3.5 rounded-xl border border-rose-950/50 bg-rose-950/15 flex flex-col justify-between">
          <div className="flex items-center justify-between text-rose-400 text-xs">
            <span className="font-medium">Down</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-300 mt-2 font-mono">{down}</div>
          <div className="text-[10px] text-rose-500/70 mt-1">Confirmed Out</div>
        </div>

        {/* SLA Violations */}
        <div className="glass-panel p-3.5 rounded-xl border border-rose-900/40 bg-rose-950/20 flex flex-col justify-between">
          <div className="flex items-center justify-between text-rose-400 text-xs">
            <span className="font-medium">Violations</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2 font-mono">{violations}</div>
          <div className="text-[10px] text-rose-400/70 mt-1">Breached Target</div>
        </div>

        {/* At-Risk Services */}
        <div className="glass-panel p-3.5 rounded-xl border border-yellow-950/40 bg-yellow-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-yellow-400 text-xs">
            <span className="font-medium">SLA At-Risk</span>
            <Flame className="w-4 h-4 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-yellow-300 mt-2 font-mono">{atRisk}</div>
          <div className="text-[10px] text-yellow-500/70 mt-1">&gt;75% Budget Used</div>
        </div>

        {/* Open Incidents */}
        <div className="glass-panel p-3.5 rounded-xl border border-indigo-950/40 bg-indigo-950/10 flex flex-col justify-between">
          <div className="flex items-center justify-between text-indigo-400 text-xs">
            <span className="font-medium">Incidents</span>
            <LifeBuoy className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-300 mt-2 font-mono">{openIncidents}</div>
          <div className="text-[10px] text-indigo-500/70 mt-1">Active NOC Tickets</div>
        </div>
      </div>

      {/* Graphical Insights (Area charts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Latency Telemetry Chart */}
        <div className="glass-panel p-4 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Response Time Telemetry (ms)
              </h2>
              <p className="text-[11px] text-gray-400">Live response latency per monitored endpoint</p>
            </div>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '11px' }}
                  formatter={(value) => [`${value} ms`, 'Response Time']}
                />
                <Bar dataKey="latency" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SLA Downtime Budget Consumption Chart */}
        <div className="glass-panel p-4 rounded-2xl border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-amber-400" />
                SLA Downtime Budget Consumption (%)
              </h2>
              <p className="text-[11px] text-gray-400">Allowed downtime budget consumption toward violation</p>
            </div>
          </div>

          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <defs>
                  <linearGradient id="budgetGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#6b7280" fontSize={10} domain={[0, 100]} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '11px' }}
                  formatter={(value) => [`${value}%`, 'Budget Consumed']}
                />
                <Area type="monotone" dataKey="budgetUsed" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#budgetGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Main Real-Time Telemetry Table */}
      <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden">
        <div className="p-4 border-b border-gray-800 flex items-center justify-between">
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Network Services Fleet Registry
            </h2>
            <p className="text-[11px] text-gray-400">
              Deterministic health verdict &amp; ML predictive risk scores
            </p>
          </div>

          <button
            onClick={() => onNavigate('services')}
            className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
          >
            <span>Manage All Services</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-950/60 text-gray-400 font-mono text-[11px] uppercase border-b border-gray-800">
              <tr>
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Health Status</th>
                <th className="py-3 px-3">Response Time</th>
                <th className="py-3 px-3">Packet Loss</th>
                <th className="py-3 px-3">Availability</th>
                <th className="py-3 px-3">SLA Target</th>
                <th className="py-3 px-3">Compliance</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-sans">
              {services.map((svc) => {
                const sla = slaOverview.find((o) => o.service_id === svc.service_id);
                const st = svc.current_state?.status || 'UNKNOWN';

                return (
                  <tr
                    key={svc.service_id}
                    onClick={() => onSelectService(svc.service_id)}
                    className="hover:bg-gray-800/40 transition-colors cursor-pointer group"
                  >
                    {/* Service Name & Target */}
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white group-hover:text-indigo-400 transition-colors">
                        {svc.name}
                      </div>
                      <div className="text-[10px] text-gray-500 font-mono truncate max-w-xs">
                        {svc.url || `${svc.target}${svc.port ? ':' + svc.port : ''}`}
                      </div>
                    </td>

                    {/* Protocol */}
                    <td className="py-3.5 px-3">
                      <span className="font-mono text-[11px] font-semibold px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700">
                        {svc.type}
                      </span>
                    </td>

                    {/* Status Badge */}
                    <td className="py-3.5 px-3">
                      <StatusBadge status={st} />
                    </td>

                    {/* Latency */}
                    <td className="py-3.5 px-3 font-mono font-medium">
                      {st === 'DOWN' ? (
                        <span className="text-rose-400 font-bold">TIMEOUT</span>
                      ) : (
                        <span className="text-gray-200">{svc.current_state?.response_time_ms} ms</span>
                      )}
                    </td>

                    {/* Packet Loss */}
                    <td className="py-3.5 px-3 font-mono text-[11px]">
                      {svc.current_state?.packet_loss_percent > 0 ? (
                        <span className="text-orange-400 font-semibold">{svc.current_state?.packet_loss_percent}%</span>
                      ) : (
                        <span className="text-gray-500">0%</span>
                      )}
                    </td>

                    {/* Availability */}
                    <td className="py-3.5 px-3 font-mono font-semibold">
                      <span className={sla?.actual_percent < svc.sla_target_percent ? 'text-rose-400' : 'text-emerald-400'}>
                        {sla ? `${sla.actual_percent.toFixed(2)}%` : '100%'}
                      </span>
                    </td>

                    {/* SLA Target */}
                    <td className="py-3.5 px-3 font-mono text-gray-400">
                      {svc.sla_target_percent}%
                    </td>

                    {/* Compliance */}
                    <td className="py-3.5 px-3">
                      {sla?.compliance_state === 'VIOLATED' ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
                          VIOLATED
                        </span>
                      ) : sla?.compliance_state === 'AT_RISK' ? (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                          AT RISK
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          COMPLIANT
                        </span>
                      )}
                    </td>

                    {/* Manual Probe Trigger */}
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={(e) => triggerManualCheck(e, svc.service_id)}
                        title="Run probe now"
                        className="p-1.5 rounded-lg bg-gray-800 hover:bg-indigo-600 hover:text-white text-gray-400 border border-gray-700 transition-colors"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
