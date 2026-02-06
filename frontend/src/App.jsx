import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-rotatedmarker';
import { Ship, AlertTriangle, Radio } from 'lucide-react';
import L from 'leaflet';

/**
 * UI Configuration for different alert levels.
 * Maps backend severity to Tailwind CSS classes.
 */
const SEVERITY_STYLES = {
    CRITICAL: {
        bg: 'bg-red-950/40',
        border: 'border-red-500',
        text: 'text-red-400',
        label: 'Critical Breach',
        pulse: 'vessel-critical-pulse' // CSS class from index.css
    },
    WARNING: {
        bg: 'bg-orange-950/40',
        border: 'border-orange-500',
        text: 'text-orange-400',
        label: 'Warning',
        pulse: ''
    },
    INFO: {
        bg: 'bg-blue-950/40',
        border: 'border-blue-500',
        text: 'text-blue-400',
        label: 'Notice',
        pulse: ''
    }
};

/**
 * Custom Leaflet icon for vessels.
 * Uses an SVG path that can be rotated based on COG (Course Over Ground).
 */
const createVesselIcon = (severity) => {
    const color = severity === 'CRITICAL' ? '#ef4444' : '#3b82f6';
    const animationClass = severity === 'CRITICAL' ? 'vessel-critical-pulse' : '';

    return L.divIcon({
        className: `custom-vessel-icon ${animationClass}`,
        html: `<div style="color: ${color};">
               <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="white" stroke-width="1">
                 <path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z" />
               </svg>
             </div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
    });
};

function App() {
    const [vessels, setVessels] = useState({});
    const [alerts, setAlerts] = useState([]);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        /**
         * 1. Initial State Fetching
         * Loads the current fleet status via REST API on startup.
         */
        console.log("📡 Fetching initial vessel fleet...");
        fetch('http://localhost:8000/vessels')
            .then(res => res.json())
            .then(result => {
                if (result.status === "success") {
                    const initialVessels = {};
                    result.data.forEach(v => {
                        initialVessels[v.mmsi] = v;
                    });
                    setVessels(initialVessels);
                    console.log(`✅ Fleet loaded: ${result.count} vessels.`);
                }
            })
            .catch(err => console.error("❌ API Fetch Error:", err));

        /**
         * 2. Live WebSocket Stream
         * Connects to the Maritime Intelligence System for real-time updates.
         */
        const socket = new WebSocket('ws://localhost:8000/ws');

        socket.onopen = () => {
            console.log("🔌 WebSocket Connection Established (Status: OPEN)");
            setIsConnected(true);
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                if (message.type === "VESSEL_UPDATE") {
                    setVessels(prev => {
                        const newVessels = { ...prev };
                        message.data.forEach(v => {
                            newVessels[v.mmsi] = v;
                        });
                        return newVessels;
                    });
                } else if (message.type === "ALERT") {
                    console.warn("🚨 SECURITY ALERT RECEIVED:", message);
                    setAlerts(prev => {
                        // Keep only the 5 most recent alerts
                        const updatedAlerts = [message, ...prev];
                        return updatedAlerts.slice(0, 5);
                    });
                }
            } catch (err) {
                console.error("❌ WS Message Parse Error:", err);
            }
        };

        socket.onclose = () => {
            console.warn("🔌 WebSocket Disconnected.");
            setIsConnected(false);
        };

        return () => socket.close();
    }, []);

    return (
        <div className="flex h-screen w-full bg-slate-900 text-white overflow-hidden font-sans">

            {/* SIDEBAR - Intelligence Panel */}
            <div className="w-80 bg-slate-800 p-6 border-r border-slate-700 overflow-y-auto shadow-xl z-10">
                <div className="flex items-center justify-between mb-8">
                    <h1 className="text-2xl font-black flex items-center gap-3 tracking-tight text-blue-400">
                        <Ship size={28}/> MARITIME VTS
                    </h1>
                    <div title={isConnected ? "Live Connection" : "Offline"}>
                        <Radio size={18} className={isConnected ? "text-green-500 animate-pulse" : "text-red-500"} />
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                            Live Security Alerts
                        </h2>
                        {alerts.length > 0 && (
                            <span className="flex h-2 w-2 rounded-full bg-red-500 animate-ping"></span>
                        )}
                    </div>

                    <div className="space-y-3">
                        {alerts.length === 0 && (
                            <div className="text-sm text-slate-500 bg-slate-900/50 p-4 rounded-lg border border-slate-700 italic text-center">
                                Monitoring Norwegian EEZ...
                            </div>
                        )}
                        {alerts.map((alert, idx) => {
                            const style = SEVERITY_STYLES[alert.data.severity] || SEVERITY_STYLES.CRITICAL;
                            return (
                                <div key={idx} className={`${style.bg} border-l-4 ${style.border} p-4 rounded-r-lg animate-in fade-in slide-in-from-left shadow-lg`}>
                                    <div className={`flex items-center gap-2 ${style.text} font-bold text-[10px] uppercase mb-1 tracking-wider`}>
                                        <AlertTriangle size={14}/> {style.label}
                                    </div>
                                    <p className="text-sm font-bold text-white tracking-tight">
                                        {alert.vessel || "Unknown Vessel"}
                                    </p>
                                    <p className="text-[10px] text-slate-400 mt-1 uppercase font-medium">
                                        Zone: {alert.data.name || "Unknown Area"}
                                    </p>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* MAP VIEW - Operational Picture */}
            <div className="flex-1 relative">
                <MapContainer center={[60.0, 4.0]} zoom={6} className="h-full w-full">
                    <TileLayer
                        attribution='&copy; CartoDB'
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    />
                    {Object.values(vessels).map((vessel) => {
                        // Check if this vessel has a recent critical alert
                        const hasCriticalAlert = alerts.some(a => a.vessel === vessel.name && a.data.severity === 'CRITICAL');

                        return (
                            <Marker
                                key={vessel.mmsi}
                                position={[vessel.lat, vessel.lon]}
                                icon={createVesselIcon(hasCriticalAlert ? 'CRITICAL' : 'INFO')}
                                rotationAngle={vessel.course || 0}
                            >
                                <Popup minWidth={200}>
                                    <div className="text-slate-900 p-2">
                                        <h3 className="font-bold border-b border-slate-200 pb-2 mb-2 text-sm uppercase">
                                            {vessel.name || 'Unnamed Vessel'}
                                        </h3>
                                        <div className="flex flex-col gap-1 text-[11px]">
                                            <div className="flex justify-between">
                                                <span className="text-slate-500 font-bold">MMSI</span>
                                                <span className="font-mono">{vessel.mmsi}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-500 font-bold">SOG (Speed)</span>
                                                <span className="text-blue-600 font-bold">{vessel.speed} kn</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-slate-500 font-bold">COG (Course)</span>
                                                <span>{vessel.course}°</span>
                                            </div>
                                        </div>
                                    </div>
                                </Popup>
                            </Marker>
                        );
                    })}
                </MapContainer>
            </div>
        </div>
    );
}

export default App;