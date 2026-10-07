import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WebSocketProvider, useWebSocket } from './context/WebSocketContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Services from './pages/Services';
import ServiceDetail from './pages/ServiceDetail';
import Incidents from './pages/Incidents';
import Alerts from './pages/Alerts';
import SLACompliance from './pages/SLACompliance';
import MLAnalytics from './pages/MLAnalytics';
import Reports from './pages/Reports';
import Simulation from './pages/Simulation';
import Settings from './pages/Settings';
import api from './api';

function MainLayout() {
  const { isAuthenticated, loading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedServiceId, setSelectedServiceId] = useState(null);
  const [badgeCounts, setBadgeCounts] = useState({ incidents: 0, alerts: 0 });
  const { subscribe } = useWebSocket();

  // Load badge counts for sidebar
  const loadBadges = async () => {
    try {
      const [incRes, altRes] = await Promise.all([
        api.get('/incidents?status=OPEN'),
        api.get('/alerts?unack_only=true')
      ]);
      setBadgeCounts({
        incidents: incRes.data.length,
        alerts: altRes.data.length
      });
    } catch {
      // ignore badge fetch failures
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadBadges();
      const unsub = subscribe('simulation_stage_changed', () => loadBadges());
      const unsubCheck = subscribe('service_checked', () => loadBadges());
      const interval = setInterval(loadBadges, 20000);
      return () => {
        unsub();
        unsubCheck();
        clearInterval(interval);
      };
    }
  }, [isAuthenticated]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F19] flex items-center justify-center text-gray-400 font-mono text-xs">
        Initializing SLA-Predict Operations Console...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  const handleSelectService = (serviceId) => {
    setSelectedServiceId(serviceId);
    setActiveTab('service-detail');
  };

  const handleNavigate = (tab) => {
    setActiveTab(tab);
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col font-sans">
      <Navbar onNavigate={handleNavigate} activeTab={activeTab} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab === 'service-detail' ? 'services' : activeTab}
          onSelect={(tab) => {
            setActiveTab(tab);
            if (tab !== 'service-detail') setSelectedServiceId(null);
          }}
          badgeCounts={badgeCounts}
        />

        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#0B0F19]/90">
          <div className="max-w-7xl mx-auto">
            {activeTab === 'dashboard' && (
              <Dashboard onSelectService={handleSelectService} onNavigate={handleNavigate} />
            )}
            {activeTab === 'services' && (
              <Services onSelectService={handleSelectService} />
            )}
            {activeTab === 'service-detail' && selectedServiceId && (
              <ServiceDetail
                serviceId={selectedServiceId}
                onBack={() => setActiveTab('services')}
              />
            )}
            {activeTab === 'incidents' && <Incidents />}
            {activeTab === 'alerts' && <Alerts />}
            {activeTab === 'sla' && (
              <SLACompliance onSelectService={handleSelectService} />
            )}
            {activeTab === 'ml' && <MLAnalytics />}
            {activeTab === 'reports' && <Reports />}
            {activeTab === 'simulation' && (
              <Simulation onSelectService={handleSelectService} />
            )}
            {activeTab === 'settings' && <Settings />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <MainLayout />
      </WebSocketProvider>
    </AuthProvider>
  );
}
