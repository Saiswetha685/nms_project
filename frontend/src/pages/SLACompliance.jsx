import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, Clock, RefreshCw, AlertTriangle, ArrowUpRight } from 'lucide-react';
import api from '../api';

export default function SLACompliance({ onSelectService }) {
  const [overview, setOverview] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadSLA = async () => {
    try {
      const res = await api.get('/sla/overview');
      setOverview(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSLA();
    const interval = setInterval(loadSLA, 20000);
    return () => clearInterval(interval);
  }, []);

  const total = overview.length;
  const compliant = overview.filter((s) => s.compliance_state === 'COMPLIANT').length;
  const atRisk = overview.filter((s) => s.compliance_state === 'AT_RISK').length;
  const violated = overview.filter((s) => s.compliance_state === 'VIOLATED').length;

  const complianceRate = total > 0 ? ((compliant / total) * 100).toFixed(1) : '100';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>SLA Compliance &amp; Downtime Budget Auditing</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Deterministic availability calculations over contractual windows and downtime budget burn
          </p>
        </div>

        <button
          onClick={loadSLA}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 text-xs font-medium"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh SLA</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="glass-panel p-4 rounded-xl border border-gray-800">
          <div className="text-gray-400 text-xs">Compliance Rate</div>
          <div className="text-2xl font-bold text-white mt-1 font-mono">{complianceRate}%</div>
          <div className="text-[10px] text-gray-500 mt-1">{compliant} of {total} targets compliant</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-emerald-950/40 bg-emerald-950/10">
          <div className="text-emerald-400 text-xs font-medium">Compliant Fleet</div>
          <div className="text-2xl font-bold text-emerald-300 mt-1 font-mono">{compliant}</div>
          <div className="text-[10px] text-emerald-500/70 mt-1">Full SLA Guarantee</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-yellow-950/40 bg-yellow-950/10">
          <div className="text-yellow-400 text-xs font-medium">At-Risk Buffer</div>
          <div className="text-2xl font-bold text-yellow-300 mt-1 font-mono">{atRisk}</div>
          <div className="text-[10px] text-yellow-500/70 mt-1">&gt;75% Downtime Burn</div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-rose-950/40 bg-rose-950/10">
          <div className="text-rose-400 text-xs font-medium">Contract Breaches</div>
          <div className="text-2xl font-bold text-rose-300 mt-1 font-mono">{violated}</div>
          <div className="text-[10px] text-rose-500/70 mt-1">Confirmed SLA Violations</div>
        </div>
      </div>

      {/* SLA Compliance Table */}
      <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-950/60 text-gray-400 font-mono text-[11px] uppercase border-b border-gray-800">
              <tr>
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-3">Type</th>
                <th className="py-3 px-3">Target SLA</th>
                <th className="py-3 px-3">Actual Availability</th>
                <th className="py-3 px-4">Downtime Budget Consumed</th>
                <th className="py-3 px-3">Budget Remaining</th>
                <th className="py-3 px-3">Compliance Verdict</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-sans">
              {overview.map((item) => {
                const isViolated = item.compliance_state === 'VIOLATED';
                const isRisk = item.compliance_state === 'AT_RISK';
                const budgetPct = Math.min(100, item.budget_consumption_percent || 0);

                return (
                  <tr
                    key={item.service_id}
                    onClick={() => onSelectService(item.service_id)}
                    className="hover:bg-gray-800/30 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-4 font-semibold text-white group-hover:text-indigo-400 transition-colors">
                      {item.service_name}
                    </td>

                    <td className="py-3.5 px-3">
                      <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-300">
                        {item.type}
                      </span>
                    </td>

                    <td className="py-3.5 px-3 font-mono font-medium text-gray-400">
                      {item.target_percent}%
                    </td>

                    <td className="py-3.5 px-3 font-mono font-bold">
                      <span className={item.actual_percent < item.target_percent ? 'text-rose-400' : 'text-emerald-400'}>
                        {item.actual_percent.toFixed(2)}%
                      </span>
                    </td>

                    {/* Progress Bar for Budget Consumption */}
                    <td className="py-3.5 px-4">
                      <div className="space-y-1">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className={isViolated ? 'text-rose-400 font-bold' : isRisk ? 'text-yellow-400 font-semibold' : 'text-gray-300'}>
                            {budgetPct.toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-1.5 w-40 bg-gray-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              isViolated
                                ? 'bg-rose-500'
                                : isRisk
                                ? 'bg-amber-400'
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${budgetPct}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-3 font-mono">
                      {item.remaining_budget_minutes?.toFixed(1)} min
                    </td>

                    <td className="py-3.5 px-3">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${
                          isViolated
                            ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                            : isRisk
                            ? 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
                            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                        }`}
                      >
                        {item.compliance_state}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <ArrowUpRight className="w-4 h-4 text-gray-400 group-hover:text-indigo-400 transition-colors ml-auto" />
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
