import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Database, Cpu, Sparkles, Bell } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-indigo-400" />
          <span>System Architecture &amp; Threshold Settings</span>
        </h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Configuration parameters for deterministic SLA rule evaluation, anti-flapping filters, and ML intelligence
        </p>
      </div>

      {/* Research Contribution Card */}
      <div className="glass-panel p-5 rounded-2xl border border-indigo-500/30 bg-indigo-950/20">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <h2 className="text-xs font-bold text-white uppercase tracking-wider mb-1">
              Academic &amp; Research Contribution Framework
            </h2>
            <p className="text-xs text-gray-300 leading-relaxed font-sans italic">
              “An explainable hybrid SLA-risk monitoring framework that extends conventional network service availability
              and SLA-compliance monitoring with rule-based risk scoring, advanced machine-learning-based short-term failure
              probability, statistical SLA-budget exhaustion estimation, and proactive alerts while preserving deterministic
              and auditable SLA decisions.”
            </p>
          </div>
        </div>
      </div>

      {/* Risk Scoring & Weights */}
      <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-4">
        <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Transparent Rule-Based SLA Risk Weights
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800">
            <div className="text-gray-400 text-[10px]">Downtime Budget Pressure</div>
            <div className="text-lg font-bold text-indigo-400 mt-1">40%</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Primary SLA factor</div>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800">
            <div className="text-gray-400 text-[10px]">Failure Burn Rate (1h)</div>
            <div className="text-lg font-bold text-amber-400 mt-1">30%</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Probe failure density</div>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800">
            <div className="text-gray-400 text-[10px]">Downtime Velocity Trend</div>
            <div className="text-lg font-bold text-cyan-400 mt-1">15%</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Acceleration slope</div>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800">
            <div className="text-gray-400 text-[10px]">Latency Degradation</div>
            <div className="text-lg font-bold text-rose-400 mt-1">15%</div>
            <div className="text-[10px] text-gray-500 mt-0.5">RTT above threshold</div>
          </div>
        </div>

        {/* Guardrails & Hysteresis */}
        <div className="p-3.5 bg-gray-950/70 rounded-xl border border-gray-800 text-xs space-y-2 text-gray-300">
          <div className="font-bold text-white text-[11px] uppercase tracking-wider font-mono">
            Mandatory Safety Guardrails &amp; Anti-Flapping
          </div>
          <p className="text-[11px] text-gray-400">
            • <b>Anti-flapping:</b> Requires 2 consecutive failures to trigger DOWN; requires 2 consecutive successes to declare RECOVERY.
          </p>
          <p className="text-[11px] text-gray-400">
            • <b>Hysteresis:</b> System enters High-Risk state at risk score &ge; 50, and exits only below 40.
          </p>
          <p className="text-[11px] text-gray-400">
            • <b>Budget Guardrails:</b> Budget &ge; 75% enforces min risk 50; Budget &ge; 90% enforces min risk 75; Budget &gt; 100% sets SLA VIOLATED and min risk 90.
          </p>
        </div>
      </div>

      {/* Backend & Database Environment Details */}
      <div className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-3">
        <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          Environment &amp; Infrastructure Runtime
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800 flex justify-between">
            <span className="text-gray-400">Database Engine:</span>
            <span className="text-emerald-400 font-semibold">MongoDB (Async Motor)</span>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800 flex justify-between">
            <span className="text-gray-400">Backend Framework:</span>
            <span className="text-white font-semibold">FastAPI + AsyncIO</span>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800 flex justify-between">
            <span className="text-gray-400">ML Ensemble:</span>
            <span className="text-cyan-400 font-semibold">XGBoost / GradientBoosting</span>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800 flex justify-between">
            <span className="text-gray-400">Forecasting Engine:</span>
            <span className="text-amber-400 font-semibold">Holt-Winters (statsmodels)</span>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800 flex justify-between">
            <span className="text-gray-400">AI Copilot:</span>
            <span className="text-indigo-400 font-semibold">Anthropic Claude (Server-Side)</span>
          </div>

          <div className="bg-gray-950/60 p-3 rounded-xl border border-gray-800 flex justify-between">
            <span className="text-gray-400">Active User:</span>
            <span className="text-white font-semibold">{user?.email} ({user?.role})</span>
          </div>
        </div>
      </div>
    </div>
  );
}
