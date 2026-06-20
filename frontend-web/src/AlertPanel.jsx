import './AlertPanel.css';

export default function AlertPanel({ dispatches }) {
  const criticalCount = dispatches.filter(d => d.severity === 'CRITICAL').length;
  const highCount = dispatches.filter(d => d.severity === 'HIGH').length;

  if (criticalCount === 0 && highCount === 0) {
    return null; // Don't show the panel if everything is fine
  }

  return (
    <div className="alert-panel glassmorphism">
      <div className="alert-header">
        <span className="alert-icon pulse">⚠️</span>
        <h3 className="alert-title">Active Emergency Alerts</h3>
      </div>
      <div className="alert-body">
        {criticalCount > 0 && (
          <div className="alert-item critical">
            <span className="alert-count">{criticalCount}</span>
            <span className="alert-label">Critical Incidents</span>
          </div>
        )}
        {highCount > 0 && (
          <div className="alert-item high">
            <span className="alert-count">{highCount}</span>
            <span className="alert-label">High Priority Incidents</span>
          </div>
        )}
      </div>
    </div>
  );
}
