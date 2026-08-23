import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import LiveFeed from './components/LiveFeed';
import AlertPanel from './components/AlertPanel';
import HotspotMap from './components/HotspotMap';

// ── Icons (inline SVG) ─────────────────────────────────────
const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
  </svg>
);

const CameraIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
  </svg>
);

const MapIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
    <line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
  </svg>
);

const BellIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
  </svg>
);

const ZapIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
  </svg>
);

// ── Stats Counter ──────────────────────────────────────────
function AnimatedCounter({ value }) {
  const [display, setDisplay] = useState(0);
  const prev = useRef(0);
  useEffect(() => {
    const diff = value - prev.current;
    if (diff === 0) return;
    const step = diff / 12;
    let current = prev.current;
    const timer = setInterval(() => {
      current += step;
      if ((step > 0 && current >= value) || (step < 0 && current <= value)) {
        setDisplay(value);
        clearInterval(timer);
      } else {
        setDisplay(Math.round(current));
      }
    }, 30);
    prev.current = value;
    return () => clearInterval(timer);
  }, [value]);
  return <>{display}</>;
}

// ── Main App ───────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    cameras: 3,
    active: 0,
    total_alerts: 0,
    weapon: 0,
    sos: 0,
    lone: 0,
  });

  const addAlert = (alert) => {
    const newAlert = { id: Date.now(), ...alert };
    setAlerts(prev => [newAlert, ...prev].slice(0, 100));
    setStats(s => {
      const updated = { ...s, total_alerts: s.total_alerts + 1 };
      if (alert.alerts?.weapon?.length) updated.weapon = s.weapon + 1;
      if (alert.alerts?.sos_gesture?.length) updated.sos = s.sos + 1;
      if (alert.alerts?.lone_woman?.length) updated.lone = s.lone + 1;
      return updated;
    });
  };

  const simulateAlert = () => {
    const types = [
      {
        severity: 'HIGH',
        camera_id: 'cam-01',
        timestamp: new Date().toISOString(),
        alerts: { sos_gesture: [{ gesture: 'BOTH_ARMS_RAISED', confidence: 0.94 }], weapon: [], lone_woman: [] },
      },
      {
        severity: 'HIGH',
        camera_id: 'cam-02',
        timestamp: new Date().toISOString(),
        alerts: { weapon: [{ type: 'knife', confidence: 0.87 }], sos_gesture: [], lone_woman: [] },
      },
      {
        severity: 'MEDIUM',
        camera_id: 'cam-03',
        timestamp: new Date().toISOString(),
        alerts: { lone_woman: [{ track_id: 4, is_high_risk_time: true, distance: 85 }], sos_gesture: [], weapon: [] },
      },
    ];
    addAlert(types[Math.floor(Math.random() * types.length)]);
  };

  return (
    <div className="app-shell">
      <div className="grid-bg" />

      {/* ── Header ──────────────────────────────────────── */}
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">
            <ShieldIcon />
          </div>
          <div>
            <div className="brand-title">Women Safety Analytics</div>
            <div className="brand-sub">SIH1605 · BEL Command Center</div>
          </div>
        </div>

        <div className="header-center">
          <button
            className={`tab-btn ${activeTab === 'live' ? 'active' : ''}`}
            onClick={() => setActiveTab('live')}
          >
            <CameraIcon /> Live Surveillance
          </button>
          <button
            className={`tab-btn ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            <MapIcon /> Threat Hotspots
          </button>
        </div>

        <div className="header-right">
          <div className="status-chip">
            <span className="status-dot" />
            SYSTEM ONLINE
          </div>
          <button className="sim-btn" onClick={simulateAlert}>
            <ZapIcon /> Simulate Alert
          </button>
        </div>
      </header>

      {/* ── Stats Bar ───────────────────────────────────── */}
      <div className="stats-bar">
        <div className="stat-cell">
          <div className="stat-label">CAMERAS ACTIVE</div>
          <div className="stat-value accent"><AnimatedCounter value={stats.active} /> / {stats.cameras}</div>
          <div className="stat-delta">Click START on feeds below</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">TOTAL ALERTS</div>
          <div className="stat-value danger"><AnimatedCounter value={stats.total_alerts} /></div>
          <div className="stat-delta">This session</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">WEAPON THREATS</div>
          <div className="stat-value danger"><AnimatedCounter value={stats.weapon} /></div>
          <div className="stat-delta">HIGH severity</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">SOS GESTURES</div>
          <div className="stat-value warning"><AnimatedCounter value={stats.sos} /></div>
          <div className="stat-delta">Distress signals</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">ISOLATION ALERTS</div>
          <div className="stat-value purple"><AnimatedCounter value={stats.lone} /></div>
          <div className="stat-delta">Lone woman detected</div>
        </div>
      </div>

      {/* ── Main Content ────────────────────────────────── */}
      <div className="main-content">

        {/* Dynamic View */}
        {activeTab === 'live' && (
          <LiveFeed
            onAlert={addAlert}
            onCameraStatusChange={(active) =>
              setStats(s => ({ ...s, active }))
            }
          />
        )}
        {activeTab === 'map' && <HotspotMap />}

        {/* Alert Panel — always visible */}
        <div className="alert-panel">
          <div className="alert-header">
            <div className="alert-header-title">
              <BellIcon /> Incident Feed
            </div>
            <div className="alert-count-badge">{alerts.length}</div>
          </div>
          <AlertPanel alerts={alerts} />
        </div>
      </div>
    </div>
  );
}
