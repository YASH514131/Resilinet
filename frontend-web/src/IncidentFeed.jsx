import { SEVERITY_COLORS } from './MapView';
import './IncidentFeed.css';

export default function IncidentFeed({ dispatches, isFiltered, severityFilter }) {
  return (
    <div id="feed-list" className="incident-feed">
      {dispatches.length === 0 && (
        <div id="feed-empty">
          {!isFiltered
            ? 'Waiting for live incidents…'
            : `No ${severityFilter} incidents.`}
        </div>
      )}

      {dispatches.map((d) => (
        <div
          key={d.incident_id}
          className="feed-card glassmorphism-card"
          style={{ borderLeft: `4px solid ${SEVERITY_COLORS[d.severity] ?? '#64748b'}` }}
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
            <span className="responder-chip">
              🚑 {d.recommended_responder_id ?? 'Unassigned'}
            </span>
            <span className="feed-card-id">
              #{d.incident_id?.slice(-6)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
