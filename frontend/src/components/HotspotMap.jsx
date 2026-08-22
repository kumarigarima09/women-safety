import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, AlertCircle } from 'lucide-react';

export default function HotspotMap() {
  const [hotspots, setHotspots] = useState([]);
  const [loading, setLoading] = useState(true);

  // New Delhi coordinates (default center)
  const center = [28.6139, 77.2090];

  useEffect(() => {
    // In a real app, this would fetch from /api/hotspots
    // For now, we simulate API delay and return dummy data
    const fetchHotspots = async () => {
      setLoading(true);
      setTimeout(() => {
        setHotspots([
          { id: 1, lat: 28.6140, lng: 77.2091, score: 0.85, count: 12, label: 'Parking Lot A' },
          { id: 2, lat: 28.6135, lng: 77.2080, score: 0.45, count: 4, label: 'Back Alley' },
          { id: 3, lat: 28.6150, lng: 77.2100, score: 0.95, count: 24, label: 'Subway Exit' },
        ]);
        setLoading(false);
      }, 800);
    };
    
    fetchHotspots();
  }, []);

  return (
    <div className="h-full w-full relative flex flex-col">
      <div className="absolute top-4 left-4 z-[400] bg-police-card/90 backdrop-blur p-3 rounded-lg border border-slate-700 shadow-lg">
        <h3 className="font-bold text-lg mb-1 flex items-center gap-2">
          <MapPin className="text-police-accent" />
          Risk Hotspots
        </h3>
        <p className="text-xs text-slate-400 mb-2">Based on historical anomaly clusters</p>
        
        <div className="flex flex-col gap-1 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500 opacity-60"></span>
            <span>High Risk (Score &gt; 0.7)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-yellow-500 opacity-60"></span>
            <span>Medium Risk (Score &lt; 0.7)</span>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center bg-slate-900">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-police-accent"></div>
        </div>
      ) : (
        <MapContainer 
          center={center} 
          zoom={16} 
          className="flex-1 w-full"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {hotspots.map(spot => {
            const isHighRisk = spot.score > 0.7;
            const color = isHighRisk ? '#ef4444' : '#eab308';
            
            return (
              <CircleMarker
                key={spot.id}
                center={[spot.lat, spot.lng]}
                radius={isHighRisk ? 30 : 15}
                pathOptions={{
                  fillColor: color,
                  fillOpacity: 0.4,
                  color: color,
                  weight: 2
                }}
              >
                <Popup className="custom-popup">
                  <div className="p-1">
                    <strong className="block mb-1 border-b border-gray-200 pb-1">{spot.label}</strong>
                    <div className="text-sm flex justify-between gap-4">
                      <span className="text-gray-500">Alerts:</span>
                      <span className="font-mono font-bold">{spot.count}</span>
                    </div>
                    <div className="text-sm flex justify-between gap-4">
                      <span className="text-gray-500">Risk Score:</span>
                      <span className={`font-mono font-bold ${isHighRisk ? 'text-red-600' : 'text-yellow-600'}`}>
                        {(spot.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      )}
    </div>
  );
}
