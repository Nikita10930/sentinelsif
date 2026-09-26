import React from 'react';

function AlertsList({ alerts = [] }) {
  const sortedAlerts = [...alerts].sort((a, b) => b.risk_score - a.risk_score);

  return (
    <div className="panel alerts-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <span className="panel-indicator red-dot pulse-red"></span>
          <h3>ACTIVE FACILITY ALERTS // HIGH-RISK THREAT REGIONS</h3>
        </div>
        <span className="alert-count-pill font-mono">
          {sortedAlerts.length} CRITICAL
        </span>
      </div>

      {sortedAlerts.length === 0 ? (
        <div className="empty-panel-state alerts-empty">
          <div className="empty-icon">🛡️</div>
          <p className="empty-title">ALL FACILITY REGIONS NORMAL</p>
                  <p className="empty-sub">
            Zero active zones exceed the High Risk threshold (&gt; 8.0). Current safety precursor levels are within accepted operating limits.
          </p>
        </div>
      ) : (
        <div className="alerts-list">
          {sortedAlerts.map((alert, idx) => (
            <div key={`${alert.department}-${alert.location}-${idx}`} className="alert-item">
              <div className="alert-item-main">
                <div className="alert-badges font-mono">
                  <span className="badge-critical">CRITICAL THREAT</span>
                  <span className="badge-dept">{alert.department}</span>
                </div>
                <h4 className="alert-location">{alert.location}</h4>
                <div className="alert-metrics font-mono">
                  <span>
                    INCIDENTS: <strong>{alert.report_count}</strong>
                  </span>
                  &bull;
                  <span>
                    LAST OBSERVED:{' '}
                    <strong>{alert.most_recent_report_date || 'RECENT'}</strong>
                  </span>
                </div>
              </div>
              <div className="alert-score-box font-mono">
                <span className="score-label">DECAYED RISK</span>
                <span className="score-value">{alert.risk_score.toFixed(1)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AlertsList;
