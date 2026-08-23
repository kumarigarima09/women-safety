import React from 'react';

// ── Icons ──────────────────────────────────────────────────
const WeaponIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6"/><path d="M2 14l6 6"/><path d="M20 10l-1.5 1.5"/>
  </svg>
);

const HandIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M18 11V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v0"/><path d="M14 10V4a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v2"/><path d="M10 10.5V6a2 2 0 0 0-2-2v0a2 2 0 0 0-2 2v8"/><path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>
  </svg>
);

const PersonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
  </svg>
);

const PinIcon = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
  </svg>
);

const ClockIcon = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
  </svg>
);

function getAlertMeta(alert) {
  if (alert.alerts?.weapon?.length) {
    return {
      type: 'weapon',
      icon: <WeaponIcon />,
      title: `WEAPON DETECTED — ${alert.alerts.weapon[0].type?.toUpperCase()}`,
      detail: `Confidence: ${(alert.alerts.weapon[0].confidence * 100).toFixed(0)}%`,
      severity: 'high',
    };
  }
  if (alert.alerts?.sos_gesture?.length) {
    return {
      type: 'sos',
      icon: <HandIcon />,
      title: `SOS GESTURE — ${alert.alerts.sos_gesture[0].gesture?.replace(/_/g, ' ')}`,
      detail: `Confidence: ${(alert.alerts.sos_gesture[0].confidence * 100).toFixed(0)}%`,
      severity: 'high',
    };
  }
  if (alert.alerts?.lone_woman?.length) {
    return {
      type: 'lone',
      icon: <PersonIcon />,
      title: 'LONE WOMAN — ISOLATED ZONE',
      detail: `Distance: ${alert.alerts.lone_woman[0].distance?.toFixed(0)}px from nearest person`,
      severity: 'med',
    };
  }
  return { type: 'sos', icon: <HandIcon />, title: 'ANOMALY DETECTED', detail: '—', severity: 'med' };
}

export default function AlertPanel({ alerts }) {
  if (!alerts?.length) {
    return (
      <div className="alert-feed">
        <div className="alert-empty">
          <div className="alert-empty-icon">🛡</div>
          <div className="alert-empty-text">
            NO ACTIVE THREATS<br />
            <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>System monitoring all zones</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="alert-feed">
      {alerts.map((alert) => {
        const meta = getAlertMeta(alert);
        const time = new Date(alert.timestamp).toLocaleTimeString('en-IN', {
          hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
        });

        return (
          <div key={alert.id} className={`alert-card ${meta.type}`}>
            <div className="alert-card-header">
              <span className="alert-card-icon">{meta.icon}</span>
              <span className="alert-card-title">{meta.title}</span>
              <span className={`severity-chip ${meta.severity}`}>
                {meta.severity === 'high' ? 'HIGH' : 'MED'}
              </span>
            </div>

            <div style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: 6, paddingLeft: 24 }}>
              {meta.detail}
            </div>

            <div className="alert-card-meta">
              <span><PinIcon /> {alert.camera_id?.toUpperCase()}</span>
              <span><ClockIcon /> {time}</span>
            </div>

            {meta.severity === 'high' && (
              <div className="alert-card-actions">
                <button className="action-btn dismiss">Dismiss</button>
                <button className="action-btn dispatch">⚡ Dispatch Patrol</button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
