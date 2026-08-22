import React from 'react';
import { AlertTriangle, Clock, MapPin, UserX, Hand } from 'lucide-react';

export default function AlertPanel({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-500">
        <ShieldCheck className="w-12 h-12 mb-2 opacity-20" />
        <p>No active alerts</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <AlertCard key={alert.id || alert.timestamp} alert={alert} />
      ))}
    </div>
  );
}

// Just a dummy icon since lucide doesn't have ShieldCheck imported above
const ShieldCheck = (props) => (
  <svg {...props} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

function AlertCard({ alert }) {
  const time = new Date(alert.timestamp).toLocaleTimeString();
  
  let title = "Unknown Alert";
  let icon = <AlertTriangle />;
  let colorClass = "border-slate-500 text-slate-500";
  let bgClass = "bg-slate-800";
  
  if (alert.alerts?.weapon?.length > 0) {
    title = `WEAPON DETECTED (${alert.alerts.weapon[0].type})`;
    colorClass = "border-red-500 text-red-500";
    bgClass = "bg-red-950/30";
    icon = <AlertTriangle className="animate-pulse" />;
  } else if (alert.alerts?.sos_gesture?.length > 0) {
    title = `SOS GESTURE: ${alert.alerts.sos_gesture[0].gesture.replace(/_/g, ' ')}`;
    colorClass = "border-orange-500 text-orange-500";
    bgClass = "bg-orange-950/30";
    icon = <Hand className="animate-pulse" />;
  } else if (alert.alerts?.lone_woman?.length > 0) {
    title = "ISOLATED WOMAN IN DARK ZONE";
    colorClass = "border-yellow-500 text-yellow-500";
    bgClass = "bg-yellow-950/30";
    icon = <UserX />;
  }

  return (
    <div className={`p-3 rounded border-l-4 ${colorClass} ${bgClass} shadow-md`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-full bg-slate-900 ${colorClass.split(' ')[1]}`}>
          {icon}
        </div>
        <div className="flex-1">
          <h4 className="font-bold text-sm text-slate-200">{title}</h4>
          
          <div className="mt-2 flex flex-col gap-1 text-xs text-slate-400">
            <div className="flex items-center gap-1">
              <MapPin size={12} />
              <span>Camera: <span className="text-slate-300 font-mono">{alert.camera_id}</span></span>
            </div>
            <div className="flex items-center gap-1">
              <Clock size={12} />
              <span>{time}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* If it's a high severity alert, we might want an action button */}
      {alert.severity === 'HIGH' && (
        <div className="mt-3 pt-2 border-t border-slate-700/50 flex justify-end gap-2">
          <button className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-xs rounded transition-colors">
            Dismiss
          </button>
          <button className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded transition-colors alert-pulse">
            DISPATCH PATROL
          </button>
        </div>
      )}
    </div>
  );
}
