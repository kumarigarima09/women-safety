import React, { useState, useEffect, useRef } from 'react';

const WS_BASE = 'ws://localhost:8000/ws/stream';

const CAMERAS = [
  { id: 'cam-01', name: 'Main Gate',   url: '0',               isolated: false },
  { id: 'cam-02', name: 'Parking Lot', url: 'rtsp://localhost', isolated: true  },
  { id: 'cam-03', name: 'Back Alley',  url: 'rtsp://localhost', isolated: true  },
  { id: 'cam-04', name: 'Stairwell',   url: 'rtsp://localhost', isolated: true  },
];

export default function LiveFeed({ onAlert, onCameraStatusChange }) {
  const [activeCams, setActiveCams] = useState(new Set());

  const toggle = (id, start) => {
    setActiveCams(prev => {
      const next = new Set(prev);
      start ? next.add(id) : next.delete(id);
      onCameraStatusChange?.(next.size);
      return next;
    });
  };

  return (
    <div className="feed-panel fade-in">
      <div className="panel-title">
        <span>◉</span> Live Camera Grid
        <div className="panel-title-line" />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          {activeCams.size}/{CAMERAS.length} ACTIVE
        </span>
      </div>

      <div className="cam-grid">
        {CAMERAS.map(cam => (
          <CameraStream
            key={cam.id}
            camera={cam}
            onAlert={onAlert}
            onStatusChange={(live) => toggle(cam.id, live)}
          />
        ))}
      </div>
    </div>
  );
}

function CameraStream({ camera, onAlert, onStatusChange }) {
  const [status, setStatus] = useState('offline'); // offline | connecting | live
  const [frameSrc, setFrameSrc] = useState(null);
  const [hasAlert, setHasAlert] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => () => stopStream(), []);

  const startStream = () => {
    setStatus('connecting');
    wsRef.current = new WebSocket(`${WS_BASE}/${camera.id}`);

    wsRef.current.onopen = () => {
      setStatus('live');
      onStatusChange?.(true);
      wsRef.current.send(JSON.stringify({ stream_url: camera.url, is_isolated: camera.isolated }));
    };

    wsRef.current.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.frame) setFrameSrc(`data:image/jpeg;base64,${data.frame}`);
        if (data.has_alert) {
          setHasAlert(true);
          onAlert?.(data);
          setTimeout(() => setHasAlert(false), 3000);
        }
      } catch {}
    };

    wsRef.current.onclose = () => {
      setStatus('offline');
      setFrameSrc(null);
      setHasAlert(false);
      onStatusChange?.(false);
    };

    wsRef.current.onerror = () => setStatus('offline');
  };

  const stopStream = () => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus('offline');
    setFrameSrc(null);
    setHasAlert(false);
    onStatusChange?.(false);
  };

  return (
    <div className={`cam-card ${hasAlert ? 'alert-active' : ''}`}>
      {/* Video Area */}
      <div className="cam-video-area">
        {frameSrc ? (
          <img src={frameSrc} alt={`${camera.name} feed`} />
        ) : (
          <div className="cam-offline-state">
            <div className="cam-offline-icon">
              {status === 'connecting' ? '⟳' : '⬛'}
            </div>
            <div className="cam-offline-text">
              {status === 'connecting' ? 'ACQUIRING SIGNAL...' : 'FEED OFFLINE'}
            </div>
          </div>
        )}

        {/* Corner brackets */}
        <div className="cam-corner tl" />
        <div className="cam-corner tr" />
        <div className="cam-corner bl" />
        <div className="cam-corner br" />

        {/* Top overlay */}
        <div className="cam-overlay-top">
          <div className={`cam-status-dot ${status}`} />
          <span className="cam-label">{camera.name}</span>
          {camera.isolated && (
            <span style={{ fontSize: 8, color: 'var(--warning)', fontFamily: 'var(--font-mono)', letterSpacing: '0.06em' }}>
              ⚠ ISOLATED
            </span>
          )}
        </div>

        {/* Alert tag */}
        {hasAlert && (
          <div className="cam-overlay-bottom">
            <span className="alert-tag">⚡ THREAT DETECTED</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="cam-footer">
        <span className="cam-id">{camera.id.toUpperCase()} · {camera.url === '0' ? 'WEBCAM' : 'RTSP'}</span>
        {status === 'live' ? (
          <button className="cam-ctrl-btn stop" onClick={stopStream}>■ STOP</button>
        ) : (
          <button className="cam-ctrl-btn start" onClick={startStream}>▶ START</button>
        )}
      </div>
    </div>
  );
}
