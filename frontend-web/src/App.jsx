// App.jsx
//
// Global State Orchestrator & Dashboard Grid Scaffolding.
// Saurabh's ownership: shell layout, WebSocket hook wiring, global station
// fetch, pinnedCoord state, and all shared state that Vaishnav's
// IncidentFeed.jsx and AlertPanel.jsx will consume via props.

import { useState, useEffect, useCallback } from 'react';
import MapView, { SEVERITY_COLORS } from './MapView';
import { useDispatchSocket } from './useDispatchSocket';
import './App.css';

// ─── Backend URLs ─────────────────────────────────────────────────────────────
const WS_URL        = 'ws://localhost:8000/ws/dispatches';
const STATIONS_URL  = 'http://localhost:8000/stations';
const INCIDENTS_URL = 'http://localhost:8000/incidents';
const REPORTS_URL   = 'http://localhost:8000/reports';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const STATUS_META = {
  connected:     { label: 'LIVE',          color: '#22c55e' },
  connecting:    { label: 'CONNECTING…',   color: '#f59e0b' },
  reconnecting:  { label: 'RECONNECTING…', color: '#f59e0b' },
  disconnected:  { label: 'OFFLINE',       color: '#ef4444' },
  error:         { label: 'ERROR',         color: '#ef4444' },
};

function severityCount(dispatches, level) {
  return dispatches.filter((d) => d.severity === level).length;
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  // ── WebSocket live dispatches ──
  const { dispatches, connectionStatus, clearDispatches } = useDispatchSocket(WS_URL);

  // ── Static station data (fetched once) ──
  const [stations, setStations]     = useState([]);
  const [stationErr, setStationErr] = useState(null);

  // ── Historical incidents snapshot (fetched once) ──
  const [historicalIncidents, setHistoricalIncidents] = useState([]);

  // ── Pinned coordinate (set by map click) ──
  const [pinnedCoord, setPinnedCoord] = useState(null);

  // ── Feed filter ──
  const [severityFilter, setSeverityFilter] = useState('ALL');

  // ── Fetch stations on mount ──
  useEffect(() => {
    fetch(STATIONS_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setStations)
      .catch((err) => {
        console.warn('[App] Could not fetch stations:', err);
        // Graceful fallback: use the seed data from the docs as demo stations.
        setStations([
          { id: 'hosp-001', name: 'City General Hospital',    type: 'Hospital',    latitude: 18.5204, longitude: 73.8567, capacity: 50 },
          { id: 'hosp-002', name: 'Riverside Medical Center', type: 'Hospital',    latitude: 18.5390, longitude: 73.8480, capacity: 30 },
          { id: 'fire-001', name: 'Central Fire Station',     type: 'FireStation', latitude: 18.5300, longitude: 73.8500, capacity: null },
        ]);
        setStationErr('Backend offline — showing demo stations.');
      });
  }, []);

  // ── Fetch historical incidents snapshot on mount ──
  useEffect(() => {
    fetch(INCIDENTS_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setHistoricalIncidents)
      .catch(() => {
        // Non-fatal; live dispatches will still appear via WebSocket.
      });
  }, []);

  // ── Map click → pin coordinate (null clears the pin) ──
  const handleMapClick = useCallback((latlng) => {
    setPinnedCoord(latlng);
  }, []);

  // ── POST /reports — manual dispatch ──
  const handleDispatchReport = useCallback(async (description, lat, lng) => {
    const res = await fetch(REPORTS_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description, latitude: lat, longitude: lng }),
    });
    if (!res.ok) throw new Error(`POST /reports failed: ${res.status}`);
    // Clear the pin after a successful submission.
    setPinnedCoord(null);
    return res.json();
  }, []);

  // ── Combine historical + live for display ──
  // Live dispatches have the same shape as historical incidents from the WS.
  const allIncidents = [
    ...dispatches,
    // Convert historical incidents into a partial DispatchUpdate shape so
    // they can be displayed on the map even before the WS fires.
    ...historicalIncidents.map((inc) => ({
      incident_id: inc.id,
      severity:    inc.severity ?? 'MEDIUM',
      dispatch_text: inc.description,
      latitude:    inc.latitude,
      longitude:   inc.longitude,
      category:    inc.description,
      recommended_responder_id: null,
    })),
  ];

  // De-duplicate by incident_id (live WS takes precedence).
  const seenIds = new Set();
  const dedupedIncidents = allIncidents.filter((inc) => {
    if (seenIds.has(inc.incident_id)) return false;
    seenIds.add(inc.incident_id);
    return true;
  });

  // ── Filtered feed (sidebar) ──
  const filteredFeed =
    severityFilter === 'ALL'
      ? dispatches
      : dispatches.filter((d) => d.severity === severityFilter);

  const { label: statusLabel, color: statusColor } =
    STATUS_META[connectionStatus] ?? STATUS_META.disconnected;

  return (
    <div id="app-shell">
      {/* ────────────────────────────────────────── */}
      {/*  HEADER                                   */}
      {/* ────────────────────────────────────────── */}
      <header id="app-header">
        <div id="header-brand">
          <span id="header-logo">⚡</span>
          <h1 id="header-title">ResiliNet AI</h1>
          <span id="header-subtitle">Command Center</span>
        </div>

        {/* Stats row */}
        <div id="header-stats">
          {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <div key={sev} className="stat-chip">
              <span
                className="stat-dot"
                style={{ background: SEVERITY_COLORS[sev] }}
              />
              <span className="stat-label">{sev}</span>
              <span className="stat-count">{severityCount(dispatches, sev)}</span>
            </div>
          ))}
        </div>

        {/* Connection status indicator */}
        <div id="status-indicator">
          <span
            id="status-dot"
            style={{
              background: statusColor,
              animation:
                connectionStatus === 'connected'
                  ? 'status-pulse 2s ease-in-out infinite'
                  : 'none',
            }}
          />
          <span id="status-label" style={{ color: statusColor }}>
            {statusLabel}
          </span>
          <span id="ws-label">WebSocket Stream</span>
        </div>
      </header>

      {stationErr && (
        <div id="station-warn">
          ⚠ {stationErr}
        </div>
      )}

      {/* ────────────────────────────────────────── */}
      {/*  MAIN GRID                                */}
      {/* ────────────────────────────────────────── */}
      <div id="app-grid">
        {/* ── MAP PANEL ── */}
        <main id="map-panel">
          <MapView
            dispatches={dedupedIncidents}
            stations={stations}
            pinnedCoord={pinnedCoord}
            onMapClick={handleMapClick}
            onDispatchReport={handleDispatchReport}
          />
        </main>

        {/* ── SIDEBAR ── */}
        {/*
          NOTE FOR VAISHNAV:
          Replace the <aside id="sidebar"> content below with:
            <IncidentFeed dispatches={filteredFeed} />
            <AlertPanel dispatches={dispatches} />
          Both components receive the live `dispatches` array from the
          shared WebSocket hook above.
        */}
        <aside id="sidebar">
          {/* ── Feed Header ── */}
          <div id="sidebar-header">
            <h2 id="sidebar-title">Live Dispatches</h2>
            <button
              id="clear-feed-btn"
              onClick={clearDispatches}
              disabled={dispatches.length === 0}
            >
              Clear
            </button>
          </div>

          {/* ── Severity Filter ── */}
          <div id="severity-filters">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                className={`filter-btn ${severityFilter === sev ? 'active' : ''}`}
                style={
                  sev !== 'ALL' && severityFilter === sev
                    ? { borderColor: SEVERITY_COLORS[sev], color: SEVERITY_COLORS[sev] }
                    : {}
                }
                onClick={() => setSeverityFilter(sev)}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* ── Dispatch Feed ── */}
          <div id="feed-list">
            {filteredFeed.length === 0 && (
              <div id="feed-empty">
                {dispatches.length === 0
                  ? 'Waiting for live incidents…'
                  : `No ${severityFilter} incidents.`}
              </div>
            )}

            {filteredFeed.map((d) => (
              <div
                key={d.incident_id}
                className="feed-card"
                style={{ borderLeft: `3px solid ${SEVERITY_COLORS[d.severity] ?? '#64748b'}` }}
              >
                <div className="feed-card-top">
                  <span
                    className={`badge badge-${d.severity}`}
                  >
                    {d.severity}
                  </span>
                  <span className="feed-card-category">{d.category}</span>
                </div>
                <p className="feed-card-text">{d.dispatch_text}</p>
                <div className="feed-card-meta">
                  <span>
                    🚑 {d.recommended_responder_id ?? 'Unassigned'}
                  </span>
                  <span className="feed-card-id">
                    #{d.incident_id?.slice(-6)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
