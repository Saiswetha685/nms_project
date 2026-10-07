import React, { useState, useEffect } from 'react';
import { FileText, Download, RefreshCw, FileSpreadsheet, ShieldCheck, Printer } from 'lucide-react';
import api from '../api';

export default function Reports() {
  const [activeReport, setActiveReport] = useState('executive');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadReport = async () => {
    setLoading(true);
    try {
      let endpoint = '/reports/executive-summary';
      if (activeReport === 'sla') endpoint = '/reports/sla';
      else if (activeReport === 'availability') endpoint = '/reports/availability';
      else if (activeReport === 'response') endpoint = '/reports/response-time';
      else if (activeReport === 'incidents') endpoint = '/reports/incidents';
      else if (activeReport === 'risk') endpoint = '/reports/predictive-risk';

      const res = await api.get(endpoint);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [activeReport]);

  const handleExportCSV = () => {
    const type = activeReport === 'sla' ? 'sla' : activeReport === 'availability' ? 'availability' : 'risk';
    window.open(`/api/reports/export/csv?type=${type}`, '_blank');
  };

  const handleExportPDF = () => {
    window.open('/api/reports/export/pdf', '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header & Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            <span>Audit Reports &amp; Compliance Exports</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Export formal SLA audits, availability records, and executive compliance reports
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gray-900 hover:bg-gray-800 text-gray-200 border border-gray-700 text-xs font-semibold cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF Audit</span>
          </button>
        </div>
      </div>

      {/* Report Switcher Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {[
          { id: 'executive', label: 'Executive Summary' },
          { id: 'sla', label: 'SLA Compliance' },
          { id: 'availability', label: 'Fleet Availability' },
          { id: 'response', label: 'Latency / Response Time' },
          { id: 'incidents', label: 'NOC Incidents Log' },
          { id: 'risk', label: 'Predictive Risk Audit' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveReport(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
              activeReport === tab.id
                ? 'bg-indigo-600 text-white font-semibold'
                : 'bg-gray-900 text-gray-400 hover:text-white border border-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Report Content View */}
      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-400 gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-indigo-400" />
          <span className="text-xs">Generating report data...</span>
        </div>
      ) : activeReport === 'executive' && data ? (
        <div className="space-y-4">
          <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
            <div className="border-b border-gray-800 pb-3 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white">Executive Operations &amp; SLA Compliance Brief</h2>
                <p className="text-xs text-gray-400 font-mono">
                  Generated {new Date(data.generated_at).toUTCString()}
                </p>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                AUDIT READY
              </span>
            </div>

            <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800 text-xs text-gray-200 leading-relaxed font-sans">
              {data.executive_narrative}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-950/60 p-3 rounded-lg border border-gray-800 font-mono text-center">
                <div className="text-[10px] text-gray-400">Total Services</div>
                <div className="text-lg font-bold text-white mt-1">{data.total_services}</div>
              </div>
              <div className="bg-gray-950/60 p-3 rounded-lg border border-gray-800 font-mono text-center">
                <div className="text-[10px] text-gray-400">Aggregate Availability</div>
                <div className="text-lg font-bold text-emerald-400 mt-1">
                  {data.average_availability_percent}%
                </div>
              </div>
              <div className="bg-gray-950/60 p-3 rounded-lg border border-gray-800 font-mono text-center">
                <div className="text-[10px] text-gray-400">SLA Violations</div>
                <div className="text-lg font-bold text-rose-400 mt-1">{data.sla_violations_count}</div>
              </div>
              <div className="bg-gray-950/60 p-3 rounded-lg border border-gray-800 font-mono text-center">
                <div className="text-[10px] text-gray-400">Active Incidents</div>
                <div className="text-lg font-bold text-amber-400 mt-1">{data.active_incidents_count}</div>
              </div>
            </div>

            <div className="pt-2">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                Operational Attention Areas
              </h3>
              <div className="space-y-1.5">
                {data.attention_areas?.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs text-gray-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : Array.isArray(data) ? (
        <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="bg-gray-950/60 text-gray-400 font-mono text-[11px] uppercase border-b border-gray-800">
                <tr>
                  {Object.keys(data[0] || {}).map((key) => (
                    <th key={key} className="py-3 px-4">
                      {key.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60 font-sans">
                {data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-800/30">
                    {Object.values(row).map((val, cIdx) => (
                      <td key={cIdx} className="py-3 px-4 font-mono text-xs text-gray-200">
                        {typeof val === 'number'
                          ? val.toFixed(2)
                          : typeof val === 'object'
                          ? JSON.stringify(val)
                          : String(val)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 text-xs text-gray-400">
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
