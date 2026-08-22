import React, { useState, useEffect } from 'react';
import LiveFeed from './components/LiveFeed';
import AlertPanel from './components/AlertPanel';
import HotspotMap from './components/HotspotMap';
import { Shield, Activity, Map as MapIcon, Bell } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [alerts, setAlerts] = useState([]);
  
  // Dummy data for testing the UI without backend
  const addDummyAlert = () => {
    const newAlert = {
      id: Date.now(),
      camera_id: 'cam-01',
      severity: 'HIGH',
      timestamp: new Date().toISOString(),
      alerts: {
        sos_gesture: [{ gesture: 'BOTH_ARMS_RAISED', confidence: 0.92 }],
        weapon: [],
        lone_woman: []
      }
    };
    setAlerts(prev => [newAlert, ...prev].slice(0, 50));
  };

  return (
    <div className="min-h-screen bg-police-dark flex flex-col">
      {/* Header */}
      <header className="bg-police-card border-b border-slate-700 p-4 shadow-lg sticky top-0 z-50">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-police-accent" />
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
              SIH1605 Surveillance Control
            </h1>
          </div>
          
          <div className="flex space-x-4">
            <button 
              onClick={addDummyAlert}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
            >
              Simulate Alert
            </button>
            <div className="flex items-center space-x-2 text-slate-300">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </span>
              <span className="text-sm font-medium">System Online</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto p-4 flex gap-6">
        {/* Left Column: Nav + Dynamic Content */}
        <div className="flex-1 flex flex-col gap-4">
          
          {/* Tabs */}
          <div className="flex space-x-2 bg-police-card p-2 rounded-lg shadow">
            <button 
              onClick={() => setActiveTab('live')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${activeTab === 'live' ? 'bg-police-accent text-white' : 'text-slate-400 hover:text-white hover:bg-slate-700'}`}
            >
              <Activity size={18} />
              <span>Live Feeds</span>
            </button>
            <button 
              onClick={() => setActiveTab('map')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${activeTab === 'map' ? 'bg-police-accent text-white' : 'text-slate-400 hover:text-white hover:bg-slate-700'}`}
            >
              <MapIcon size={18} />
              <span>Hotspot Map</span>
            </button>
          </div>

          {/* Dynamic View */}
          <div className="flex-1 bg-police-card rounded-lg shadow-lg border border-slate-700 overflow-hidden min-h-[600px]">
            {activeTab === 'live' && <LiveFeed onAlert={(alert) => setAlerts(prev => [alert, ...prev].slice(0, 50))} />}
            {activeTab === 'map' && <HotspotMap />}
          </div>
          
        </div>

        {/* Right Column: Alert Panel */}
        <div className="w-96 flex-shrink-0 flex flex-col bg-police-card rounded-lg shadow-lg border border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800">
            <h2 className="text-lg font-semibold flex items-center space-x-2">
              <Bell size={20} className="text-police-alert" />
              <span>Active Alerts</span>
            </h2>
            <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded-full text-xs font-bold">
              {alerts.length} NEW
            </span>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2">
            <AlertPanel alerts={alerts} />
          </div>
        </div>
        
      </main>
    </div>
  );
}

export default App;
