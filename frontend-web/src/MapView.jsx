// MapView.jsx
//
// Geospatial canvas for the ResiliNet AI Command Center.
//
// Responsibilities (Saurabh's ownership):
//   1. Render a Leaflet map using OpenStreetMap tile servers.
//   2. Render emergency asset STATIONS as static markers, color-coded by type.
//   3. Map live incoming WebSocket dispatches as pulsing incident vectors.
//   4. Handle interactive map clicks to lock a coordinate pin and open the
//      manual report dispatch form (POST /report).

import { useState, useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Marker,
  Popup,
  useMapEvents,
} from 'react-leaflet';
import L from 'leaflet';

// ─── Severity → color mapping (mirrors the docs and mobile app) ──────────────
export const SEVERITY_COLORS = {
  LOW:      '#3b82f6', // blue
  MEDIUM:   '#f59e0b', // amber
  HIGH:     '#ef4444', // red
  CRITICAL: '#7c3aed', // deep violet
};

// ─── Station type → color mapping ────────────────────────────────────────────
const STATION_COLORS = {
  Hospital:    '#10b981', // emerald
  FireStation: '#f97316', // orange
  Police:      '#6366f1', // indigo
  default:     '#64748b', // slate
};

// Custom SVG pin icon for the "click-to-pin" coordinate marker.
const pinIcon = L.divIcon({
  className: '',
  html: `<div style="
    width: 22px; height: 22px;
    background: #e11d48;
    border: 3px solid #fff;
    border-radius: 50%;
    box-shadow: 0 0 0 3px #e11d48, 0 2px 8px rgba(0,0,0,0.5);
  "></div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

// ─── Inner component: handles map click events ────────────────────────────────
function MapClickHandler({ onMapClick }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng);
    },
  });
  return null;
}

// ─── Pulsing ring overlay rendered as CSS animation ──────────────────────────
// We use a plain <div> injected into each CircleMarker via a Leaflet DivIcon
// for the outer pulse ring, while the core dot is the CircleMarker itself.

// ─── Main component ───────────────────────────────────────────────────────────
export default function MapView({
  dispatches,
  stations,
  pinnedCoord,
  onMapClick,
  onDispatchReport,  // (description: string, lat: number, lng: number) => void
}) {
  // City center from the docs seed data (Pune, India).
  const CITY_CENTER = [18.5204, 73.8567];

  const [reportForm, setReportForm] = useState({ description: '' });
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState('');

  // When pin changes, reset the form.
  useEffect(() => {
    setReportForm({ description: '' });
    setSubmitMsg('');
  }, [pinnedCoord]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pinnedCoord || !reportForm.description.trim()) return;
    setSubmitting(true);
    setSubmitMsg('');
    try {
      await onDispatchReport(
        reportForm.description,
        pinnedCoord.lat,
        pinnedCoord.lng,
      );
      setSubmitMsg('✓ Report submitted successfully!');
      setReportForm({ description: '' });
    } catch (err) {
      setSubmitMsg('✗ Failed to submit. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%' }}>
      <MapContainer
        center={CITY_CENTER}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        {/* ── Base tile layer — OpenStreetMap (no API key needed) ── */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* ── Map click handler ── */}
        <MapClickHandler onMapClick={onMapClick} />

        {/* ── Static station markers (color-coded by type) ── */}
        {stations.map((station) => {
          const color = STATION_COLORS[station.type] ?? STATION_COLORS.default;
          return (
            <CircleMarker
              key={station.id}
              center={[station.latitude, station.longitude]}
              radius={9}
              pathOptions={{
                color: '#fff',
                weight: 2,
                fillColor: color,
                fillOpacity: 1,
              }}
            >
              <Popup>
                <div style={{ minWidth: 160 }}>
                  <strong style={{ color }}>{station.name}</strong>
                  <br />
                  <span style={{ fontSize: 12, color: '#64748b' }}>
                    {station.type}
                  </span>
                  {station.capacity && (
                    <>
                      <br />
                      <span style={{ fontSize: 12 }}>
                        Capacity: {station.capacity}
                      </span>
                    </>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* ── Live incident dispatch markers (pulsing) ── */}
        {dispatches.map((dispatch) => {
          const color = SEVERITY_COLORS[dispatch.severity] ?? '#94a3b8';
          return (
            <CircleMarker
              key={dispatch.incident_id}
              center={[dispatch.latitude, dispatch.longitude]}
              radius={12}
              pathOptions={{
                color,
                weight: 2,
                fillColor: color,
                fillOpacity: 0.25,
              }}
            >
              {/* Inner solid core */}
              <CircleMarker
                center={[dispatch.latitude, dispatch.longitude]}
                radius={6}
                pathOptions={{
                  color: '#fff',
                  weight: 1.5,
                  fillColor: color,
                  fillOpacity: 0.95,
                }}
              >
                <Popup>
                  <div style={{ minWidth: 200 }}>
                    <div
                      style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: color,
                        color: '#fff',
                        fontSize: 11,
                        fontWeight: 700,
                        marginBottom: 6,
                      }}
                    >
                      {dispatch.severity}
                    </div>
                    <br />
                    <strong style={{ fontSize: 13 }}>{dispatch.category}</strong>
                    <p style={{ fontSize: 12, margin: '4px 0', color: '#374151' }}>
                      {dispatch.dispatch_text}
                    </p>
                    <span style={{ fontSize: 11, color: '#6b7280' }}>
                      Responder: {dispatch.recommended_responder_id ?? 'Unassigned'}
                    </span>
                    <br />
                    <span style={{ fontSize: 11, color: '#6b7280' }}>
                      ID: {dispatch.incident_id}
                    </span>
                  </div>
                </Popup>
              </CircleMarker>
            </CircleMarker>
          );
        })}

        {/* ── Coordinate pin (set by map click) ── */}
        {pinnedCoord && (
          <Marker
            position={[pinnedCoord.lat, pinnedCoord.lng]}
            icon={pinIcon}
          >
            <Popup autoClose={false} closeOnClick={false}>
              <span style={{ fontSize: 12, color: '#64748b' }}>
                📍 {pinnedCoord.lat.toFixed(5)}, {pinnedCoord.lng.toFixed(5)}
              </span>
            </Popup>
          </Marker>
        )}
      </MapContainer>

      {/* ── Floating dispatch form overlay (appears when pin is set) ── */}
      {pinnedCoord && (
        <div
          style={{
            position: 'absolute',
            bottom: 32,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            background: 'rgba(15,23,42,0.96)',
            backdropFilter: 'blur(10px)',
            borderRadius: 12,
            padding: '18px 22px',
            minWidth: 320,
            maxWidth: 420,
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h3 style={{ margin: 0, color: '#f1f5f9', fontSize: 14, fontWeight: 600 }}>
              📍 Report Incident
            </h3>
            <span style={{ fontSize: 11, color: '#94a3b8' }}>
              {pinnedCoord.lat.toFixed(5)}, {pinnedCoord.lng.toFixed(5)}
            </span>
          </div>

          <form onSubmit={handleSubmit}>
            <textarea
              id="report-description"
              value={reportForm.description}
              onChange={(e) => setReportForm({ description: e.target.value })}
              placeholder="Describe the incident (e.g. Smoke visible from 3rd floor window)…"
              required
              rows={3}
              style={{
                width: '100%',
                borderRadius: 8,
                border: '1px solid rgba(255,255,255,0.12)',
                background: 'rgba(255,255,255,0.06)',
                color: '#f1f5f9',
                fontSize: 13,
                padding: '8px 12px',
                resize: 'vertical',
                boxSizing: 'border-box',
                outline: 'none',
                fontFamily: 'inherit',
              }}
            />

            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button
                type="submit"
                disabled={submitting || !reportForm.description.trim()}
                style={{
                  flex: 1,
                  padding: '8px 0',
                  borderRadius: 8,
                  border: 'none',
                  background: submitting ? '#475569' : '#e11d48',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  transition: 'background 0.2s',
                }}
              >
                {submitting ? 'Dispatching…' : 'Dispatch Report'}
              </button>
              <button
                type="button"
                onClick={() => onMapClick(null)}
                style={{
                  padding: '8px 14px',
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.12)',
                  background: 'transparent',
                  color: '#94a3b8',
                  fontSize: 13,
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>

            {submitMsg && (
              <p
                style={{
                  marginTop: 8,
                  fontSize: 12,
                  color: submitMsg.startsWith('✓') ? '#34d399' : '#f87171',
                  textAlign: 'center',
                }}
              >
                {submitMsg}
              </p>
            )}
          </form>
        </div>
      )}

      {/* ── Map click hint ── */}
      {!pinnedCoord && (
        <div
          style={{
            position: 'absolute',
            bottom: 32,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 999,
            background: 'rgba(15,23,42,0.75)',
            backdropFilter: 'blur(8px)',
            color: '#94a3b8',
            fontSize: 12,
            padding: '8px 16px',
            borderRadius: 20,
            pointerEvents: 'none',
            whiteSpace: 'nowrap',
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          Click anywhere on the map to pin a location and report an incident
        </div>
      )}
    </div>
  );
}
