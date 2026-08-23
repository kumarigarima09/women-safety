import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Seed hotspot data for demo
const DEMO_HOTSPOTS = [
  { id: 1, lat: 28.6155, lng: 77.2100, score: 0.92, count: 24, label: 'Subway Exit — Zone A', type: 'weapon' },
  { id: 2, lat: 28.6130, lng: 77.2070, score: 0.74, count: 12, label: 'Back Alley — Zone B', type: 'lone' },
  { id: 3, lat: 28.6145, lng: 77.2115, score: 0.55, count: 6,  label: 'Parking Lot — Zone C', type: 'sos' },
  { id: 4, lat: 28.6120, lng: 77.2085, score: 0.88, count: 18, label: 'Bus Stop — Zone D', type: 'weapon' },
  { id: 5, lat: 28.6165, lng: 77.2090, score: 0.42, count: 4,  label: 'Market Lane — Zone E', type: 'lone' },
];

const THREAT_COLORS = {
  weapon: '#ff2d55',
  sos:    '#ff9500',
  lone:   '#bf5af2',
};

export default function HotspotMap() {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const center = [28.6139, 77.2090];

  useEffect(() => {
    // Try API, fall back to demo data
    fetch('http://localhost:8000/api/hotspots/')
      .then(r => r.json())
      .then(data => {
        if (data.length > 0) {
          setHotspots(data.map((h, i) => ({
            ...h, label: `Cluster ${i + 1}`, type: 'weapon'
          })));
        } else {
          setHotspots(DEMO_HOTSPOTS);
        }
      })
      .catch(() => setHotspots(DEMO_HOTSPOTS))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="map-panel fade-in">
      <div className="panel-title">
        <span>◎</span> Threat Hotspot Map — New Delhi
        <div className="panel-title-line" />
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
          {hotspots.length} CLUSTERS
        </span>
      </div>

      <div className="map-container">
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', background: 'var(--bg-dark)' }}>
            <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: 28, marginBottom: 8, animation: 'blink 1s infinite' }}>◎</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.1em' }}>
                LOADING THREAT MAP...
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Legend Overlay */}
            <div className="map-legend">
              <div className="map-legend-title">
                <span>▣</span> Risk Level Legend
              </div>
              {[
                { color: '#ff2d55', label: 'WEAPON THREAT (HIGH)' },
                { color: '#ff9500', label: 'SOS GESTURE (HIGH)' },
                { color: '#bf5af2', label: 'ISOLATED WOMAN (MED)' },
              ].map(({ color, label }) => (
                <div key={label} className="legend-row">
                  <div className="legend-dot" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em' }}>{label}</span>
                </div>
              ))}
            </div>

            <MapContainer
              center={center}
              zoom={16}
              style={{ height: '100%', width: '100%' }}
              zoomControl={true}
            >
              <TileLayer
                attribution='© OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {hotspots.map(spot => {
                const color = THREAT_COLORS[spot.type] || '#00d4ff';
                const radius = Math.max(12, Math.min(50, spot.count * 2));

                return (
                  <CircleMarker
                    key={spot.id}
                    center={[spot.lat ?? spot.latitude, spot.lng ?? spot.longitude]}
                    radius={radius}
                    pathOptions={{
                      fillColor: color,
                      fillOpacity: 0.3,
                      color: color,
                      weight: 2,
                      dashArray: spot.score > 0.7 ? '' : '4 4',
                    }}
                    eventHandlers={{ click: () => setSelected(spot) }}
                  >
                    <Popup>
                      <div style={{ fontFamily: 'monospace', minWidth: 160 }}>
                        <div style={{ fontWeight: 700, borderBottom: '1px solid #eee', paddingBottom: 4, marginBottom: 6, color: color }}>
                          {spot.label}
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, fontSize: 12 }}>
                          <span style={{ color: '#666' }}>Alert Count</span>
                          <strong>{spot.count ?? spot.alert_count}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                          <span style={{ color: '#666' }}>Risk Score</span>
                          <strong style={{ color }}>{((spot.score ?? spot.risk_score) * 100).toFixed(0)}%</strong>
                        </div>
                      </div>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </>
        )}
      </div>

      {/* Hotspot table */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        flexShrink: 0,
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', padding: '8px 14px', background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid var(--border)' }}>
          {['ZONE', 'THREAT', 'ALERTS', 'RISK SCORE'].map(h => (
            <div key={h} style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>{h}</div>
          ))}
        </div>
        {hotspots.map(spot => {
          const color = THREAT_COLORS[spot.type] || '#00d4ff';
          const score = spot.score ?? spot.risk_score ?? 0;
          return (
            <div key={spot.id} style={{
              display: 'grid',
              gridTemplateColumns: '2fr 1fr 1fr 1fr',
              padding: '7px 14px',
              borderBottom: '1px solid var(--border)',
              fontSize: 11,
              fontFamily: 'var(--font-mono)',
              alignItems: 'center',
              transition: 'background 0.15s',
              cursor: 'pointer',
            }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = ''}
            >
              <span style={{ color: 'var(--text-secondary)' }}>{spot.label}</span>
              <span style={{ color, fontSize: 9, letterSpacing: '0.08em' }}>{(spot.type || 'UNKNOWN').toUpperCase()}</span>
              <span style={{ color: 'var(--text-primary)' }}>{spot.count ?? spot.alert_count}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ flex: 1, height: 3, background: 'var(--border)', borderRadius: 99 }}>
                  <div style={{ width: `${score * 100}%`, height: '100%', background: color, borderRadius: 99 }} />
                </div>
                <span style={{ color }}>{(score * 100).toFixed(0)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
