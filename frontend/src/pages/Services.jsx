import React, { useState, useEffect } from 'react';
import {
  Server,
  Plus,
  Search,
  Filter,
  Trash2,
  Edit,
  RefreshCw,
  ExternalLink,
  X,
  Check
} from 'lucide-react';
import api from '../api';
import StatusBadge from '../components/StatusBadge';
import { useAuth } from '../context/AuthContext';

export default function Services({ onSelectService }) {
  const { isAdmin } = useAuth();
  const [services, setServices] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Form fields
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'HTTP',
    target: '',
    port: '',
    url: '',
    check_interval_seconds: 30,
    timeout_seconds: 5,
    expected_response_ms: 150,
    warning_response_ms: 350,
    critical_response_ms: 700,
    sla_target_percent: 99.0,
    sla_window_days: 30,
    count_degraded_as_downtime: false,
    consecutive_failures_down: 2,
    consecutive_successes_recovery: 2,
    notification_enabled: true
  });

  const loadServices = async () => {
    try {
      const res = await api.get('/services');
      setServices(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadServices();
  }, []);

  const openAddModal = () => {
    setEditingService(null);
    setFormData({
      name: '',
      description: '',
      type: 'HTTP',
      target: '',
      port: '',
      url: '',
      check_interval_seconds: 30,
      timeout_seconds: 5,
      expected_response_ms: 150,
      warning_response_ms: 350,
      critical_response_ms: 700,
      sla_target_percent: 99.0,
      sla_window_days: 30,
      count_degraded_as_downtime: false,
      consecutive_failures_down: 2,
      consecutive_successes_recovery: 2,
      notification_enabled: true
    });
    setModalOpen(true);
  };

  const openEditModal = (svc, e) => {
    e.stopPropagation();
    setEditingService(svc);
    setFormData({
      name: svc.name,
      description: svc.description || '',
      type: svc.type,
      target: svc.target,
      port: svc.port || '',
      url: svc.url || '',
      check_interval_seconds: svc.check_interval_seconds,
      timeout_seconds: svc.timeout_seconds,
      expected_response_ms: svc.expected_response_ms,
      warning_response_ms: svc.warning_response_ms,
      critical_response_ms: svc.critical_response_ms,
      sla_target_percent: svc.sla_target_percent,
      sla_window_days: svc.sla_window_days,
      count_degraded_as_downtime: svc.count_degraded_as_downtime,
      consecutive_failures_down: svc.consecutive_failures_down,
      consecutive_successes_recovery: svc.consecutive_successes_recovery,
      notification_enabled: svc.notification_enabled
    });
    setModalOpen(true);
  };

  const handleDelete = async (sid, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this service and its telemetry?')) return;
    try {
      await api.delete(`/services/${sid}`);
      loadServices();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete service');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        port: formData.port ? parseInt(formData.port, 10) : null,
        check_interval_seconds: parseInt(formData.check_interval_seconds, 10),
        timeout_seconds: parseInt(formData.timeout_seconds, 10),
        expected_response_ms: parseFloat(formData.expected_response_ms),
        warning_response_ms: parseFloat(formData.warning_response_ms),
        critical_response_ms: parseFloat(formData.critical_response_ms),
        sla_target_percent: parseFloat(formData.sla_target_percent),
        sla_window_days: parseInt(formData.sla_window_days, 10),
        consecutive_failures_down: parseInt(formData.consecutive_failures_down, 10),
        consecutive_successes_recovery: parseInt(formData.consecutive_successes_recovery, 10)
      };

      if (editingService) {
        await api.put(`/services/${editingService.service_id}`, payload);
      } else {
        await api.post('/services', payload);
      }
      setModalOpen(false);
      loadServices();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save service');
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = services.filter((s) => {
    const matchesType = filterType === 'ALL' || s.type === filterType;
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.target.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.url && s.url.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesType && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            <span>Monitored Services Registry</span>
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Configure probe parameters, SLA thresholds, and anti-flapping filters
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={openAddModal}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Register New Service</span>
          </button>
        )}
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-3.5 rounded-xl border border-gray-800 flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search service name, hostname, URL..."
            className="w-full bg-gray-950/70 border border-gray-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* Protocol Types */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
          {['ALL', 'HTTP', 'HTTPS', 'PING', 'TCP', 'DNS'].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono font-medium transition-colors cursor-pointer ${
                filterType === type
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'bg-gray-900 text-gray-400 hover:text-gray-200 hover:bg-gray-800 border border-gray-800'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((svc) => {
          const st = svc.current_state?.status || 'UNKNOWN';
          return (
            <div
              key={svc.service_id}
              onClick={() => onSelectService(svc.service_id)}
              className="glass-panel rounded-2xl p-5 border border-gray-800 hover:border-indigo-500/50 transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-300 font-bold">
                      {svc.type}
                    </span>
                    <StatusBadge status={st} size="sm" />
                  </div>

                  {isAdmin && (
                    <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={(e) => openEditModal(svc, e)}
                        title="Edit"
                        className="p-1 rounded text-gray-400 hover:text-indigo-400 hover:bg-gray-800"
                      >
                        <Edit className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => handleDelete(svc.service_id, e)}
                        title="Delete"
                        className="p-1 rounded text-gray-400 hover:text-rose-400 hover:bg-gray-800"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                <h3 className="font-bold text-white group-hover:text-indigo-400 transition-colors text-sm">
                  {svc.name}
                </h3>
                <p className="text-[11px] text-gray-400 line-clamp-2 mt-1 mb-3">
                  {svc.description || 'Monitored network application endpoint'}
                </p>

                <div className="bg-gray-950/60 p-2.5 rounded-lg border border-gray-800/80 font-mono text-[11px] space-y-1">
                  <div className="flex justify-between text-gray-400">
                    <span>Target:</span>
                    <span className="text-gray-200 truncate max-w-[170px]">
                      {svc.url || `${svc.target}${svc.port ? ':' + svc.port : ''}`}
                    </span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>Latency:</span>
                    <span className="text-gray-200 font-semibold">
                      {st === 'DOWN' ? 'DOWN' : `${svc.current_state?.response_time_ms} ms`}
                    </span>
                  </div>
                  <div className="flex justify-between text-gray-400">
                    <span>SLA Commitment:</span>
                    <span className="text-emerald-400 font-semibold">{svc.sla_target_percent}%</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-800/80 flex items-center justify-between text-[11px] text-gray-400">
                <span>Interval: {svc.check_interval_seconds}s</span>
                <span className="text-indigo-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1 font-semibold">
                  Inspect <ExternalLink className="w-3 h-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal for Add / Edit Service */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="max-w-xl w-full bg-gray-900 border border-gray-800 rounded-2xl p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex items-center justify-between pb-4 border-b border-gray-800 mb-4">
              <h2 className="text-base font-bold text-white">
                {editingService ? `Edit Service: ${editingService.name}` : 'Register New Monitored Service'}
              </h2>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Service Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Student Portal"
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 font-medium mb-1">Probe Type *</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  >
                    <option value="HTTP">HTTP</option>
                    <option value="HTTPS">HTTPS</option>
                    <option value="PING">PING (ICMP)</option>
                    <option value="TCP">TCP Socket</option>
                    <option value="DNS">DNS Lookup</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-medium mb-1">Description</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Operational role description"
                  className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <label className="block text-gray-300 font-medium mb-1">Target (Hostname / IP) *</label>
                  <input
                    type="text"
                    required
                    value={formData.target}
                    onChange={(e) => setFormData({ ...formData, target: e.target.value })}
                    placeholder="e.g. portal.campus.edu"
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Port</label>
                  <input
                    type="number"
                    value={formData.port}
                    onChange={(e) => setFormData({ ...formData, port: e.target.value })}
                    placeholder="e.g. 443"
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  />
                </div>
              </div>

              {(formData.type === 'HTTP' || formData.type === 'HTTPS') && (
                <div>
                  <label className="block text-gray-300 font-medium mb-1">Full HTTP/HTTPS URL</label>
                  <input
                    type="url"
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    placeholder="https://portal.campus.edu/health"
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  />
                </div>
              )}

              {/* Thresholds */}
              <div className="p-3 bg-gray-950/60 rounded-xl border border-gray-800 space-y-3">
                <div className="text-[11px] font-bold text-gray-300 uppercase tracking-wider">
                  Latency Thresholds (ms)
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-gray-400 text-[10px] mb-1">Expected (ms)</label>
                    <input
                      type="number"
                      required
                      value={formData.expected_response_ms}
                      onChange={(e) => setFormData({ ...formData, expected_response_ms: e.target.value })}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg p-1.5 text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-gray-400 text-[10px] mb-1">Warning (ms)</label>
                    <input
                      type="number"
                      required
                      value={formData.warning_response_ms}
                      onChange={(e) => setFormData({ ...formData, warning_response_ms: e.target.value })}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg p-1.5 text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-gray-400 text-[10px] mb-1">Critical (ms)</label>
                    <input
                      type="number"
                      required
                      value={formData.critical_response_ms}
                      onChange={(e) => setFormData({ ...formData, critical_response_ms: e.target.value })}
                      className="w-full bg-gray-900 border border-gray-700 rounded-lg p-1.5 text-white"
                    />
                  </div>
                </div>
              </div>

              {/* SLA Configuration */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-medium mb-1">SLA Target (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="50"
                    max="100"
                    required
                    value={formData.sla_target_percent}
                    onChange={(e) => setFormData({ ...formData, sla_target_percent: e.target.value })}
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  />
                </div>
                <div>
                  <label className="block text-gray-300 font-medium mb-1">SLA Window (Days)</label>
                  <input
                    type="number"
                    required
                    value={formData.sla_window_days}
                    onChange={(e) => setFormData({ ...formData, sla_window_days: e.target.value })}
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg p-2 text-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="degradedToggle"
                  checked={formData.count_degraded_as_downtime}
                  onChange={(e) => setFormData({ ...formData, count_degraded_as_downtime: e.target.checked })}
                  className="rounded border-gray-700 bg-gray-950 text-indigo-600"
                />
                <label htmlFor="degradedToggle" className="text-gray-300 text-xs">
                  Count degraded (Critical latency) checks toward Downtime Budget
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
                >
                  {submitting ? 'Saving...' : editingService ? 'Update Service' : 'Create Service'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
