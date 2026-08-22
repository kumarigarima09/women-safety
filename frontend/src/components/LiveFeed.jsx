import React, { useState, useEffect, useRef } from 'react';
import { Camera, AlertTriangle, Play, Square } from 'lucide-react';

const WEBSOCKET_URL = "ws://localhost:8000/ws/stream";

export default function LiveFeed({ onAlert }) {
  const [cameras, setCameras] = useState([
    { id: 'cam-01', name: 'Main Gate', url: '0', active: false },
    { id: 'cam-02', name: 'Parking Lot', url: 'rtsp://mock', active: false },
  ]);

  return (
    <div className="p-4 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Camera className="text-police-accent" /> Live Surveillance Feeds
        </h2>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1">
        {cameras.map(cam => (
          <CameraStream 
            key={cam.id} 
            camera={cam} 
            onAlert={onAlert}
          />
        ))}
      </div>
    </div>
  );
}

function CameraStream({ camera, onAlert }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [frameSrc, setFrameSrc] = useState(null);
  const [status, setStatus] = useState('offline');
  const wsRef = useRef(null);

  useEffect(() => {
    return () => stopStream(); // cleanup on unmount
  }, []);

  const startStream = () => {
    setStatus('connecting');
    wsRef.current = new WebSocket(`${WEBSOCKET_URL}/${camera.id}`);
    
    wsRef.current.onopen = () => {
      setStatus('live');
      setIsPlaying(true);
      // Send config payload to backend
      wsRef.current.send(JSON.stringify({ 
        stream_url: camera.url,
        is_isolated: false 
      }));
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.frame) {
          setFrameSrc(`data:image/jpeg;base64,${data.frame}`);
        }
        if (data.has_alert) {
          onAlert(data);
        }
      } catch (err) {
        console.error("Frame decode error", err);
      }
    };

    wsRef.current.onclose = () => {
      setStatus('offline');
      setIsPlaying(false);
      setFrameSrc(null);
    };
  };

  const stopStream = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('offline');
    setIsPlaying(false);
    setFrameSrc(null);
  };

  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden border border-slate-700 relative flex flex-col group">
      {/* Video Area */}
      <div className="flex-1 relative bg-black flex items-center justify-center min-h-[300px]">
        {frameSrc ? (
          <img src={frameSrc} alt={`${camera.name} feed`} className="w-full h-full object-contain" />
        ) : (
          <div className="text-slate-600 flex flex-col items-center">
            <Camera size={48} className="mb-2 opacity-50" />
            <span>{status === 'connecting' ? 'Connecting...' : 'Feed Offline'}</span>
          </div>
        )}
        
        {/* Status indicator overlay */}
        <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/60 px-2 py-1 rounded backdrop-blur-sm">
          <span className={`h-2 w-2 rounded-full ${status === 'live' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
          <span className="text-xs font-mono font-semibold uppercase">{camera.name}</span>
        </div>
      </div>

      {/* Controls Area */}
      <div className="bg-slate-800 p-2 flex justify-between items-center border-t border-slate-700 opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-0 w-full">
        <span className="text-xs font-mono text-slate-400">{camera.id} | {camera.url}</span>
        <button 
          onClick={isPlaying ? stopStream : startStream}
          className={`flex items-center gap-1 px-3 py-1 rounded text-sm font-semibold transition-colors ${
            isPlaying ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
          }`}
        >
          {isPlaying ? <><Square size={14} /> Stop</> : <><Play size={14} /> Start</>}
        </button>
      </div>
    </div>
  );
}
