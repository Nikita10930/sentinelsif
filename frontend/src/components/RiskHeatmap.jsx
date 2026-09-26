import React, { useState } from 'react';

function RiskHeatmap({ data = [] }) {
  const [selectedZone, setSelectedZone] = useState(null);
  const [hoveredZone, setHoveredZone] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const getRiskColor = (level) => {
    switch (level) {
      case 'High Risk':
        return 'cell-high';
      case 'Medium Risk':
        return 'cell-medium';
      case 'Low Risk':
      default:
        return 'cell-low';
    }
  };

  const handleMouseMove = (e, item) => {
    setHoveredZone(item);
    setTooltipPos({ x: e.clientX, y: e.clientY });
  };

  const handleMouseLeave = () => {
    setHoveredZone(null);
  };

  const toggleSelect = (item) => {
    if (selectedZone && selectedZone.department === item.department && selectedZone.location === item.location) {
      setSelectedZone(null);
    } else {
      setSelectedZone(item);
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="panel heatmap-panel">
        <div className="panel-header">
          <div className="panel-title-wrap">
            <span className="panel-indicator cyan-dot"></span>
            <h3>FACILITY RISK HEATMAP // DEPT &times; LOCATION MATRIX</h3>
          </div>
        </div>
        <div className="empty-panel-state">
          <div className="empty-icon">🗺️</div>
          <p className="empty-title">NO FACILITY TELEMETRY DATA AVAILABLE</p>
          <p className="empty-sub">
            The database currently has no safety observations recorded. Submit a report to initialize the operational matrix.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel heatmap-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <span className="panel-indicator cyan-dot"></span>
          <h3>FACILITY RISK HEATMAP // DEPT &times; LOCATION MATRIX</h3>
        </div>
           <div className="heatmap-legend">
          <span className="legend-item"><span className="legend-box cell-low"></span> Low (&le; 4.0)</span>
          <span className="legend-item"><span className="legend-box cell-medium"></span> Medium (4.1 &ndash; 8.0)</span>
          <span className="legend-item"><span className="legend-box cell-high"></span> High (&gt; 8.0)</span>
        </div>
      </div>

      <div className="heatmap-grid">
        {data.map((item, idx) => {
          const isSelected =
            selectedZone &&
            selectedZone.department === item.department &&
            selectedZone.location === item.location;

          return (
            <div
              key={`${item.department}-${item.location}-${idx}`}
              className={`heatmap-cell ${getRiskColor(item.risk_level)} ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleSelect(item)}
              onMouseMove={(e) => handleMouseMove(e, item)}
              onMouseLeave={handleMouseLeave}
            >
              <div className="cell-top">
                <span className="cell-dept">{item.department}</span>
                <span className="cell-badge font-mono">{item.risk_level}</span>
              </div>
              <div className="cell-loc">{item.location}</div>
              <div className="cell-bottom">
                <span className="cell-score font-mono">
                  RISK: <strong>{item.risk_score.toFixed(1)}</strong>
                </span>
                <span className="cell-count font-mono">{item.report_count} rep</span>
              </div>
              <div className="cell-scanline"></div>
            </div>
          );
        })}
      </div>

      {/* Hover Floating Tooltip */}
      {hoveredZone && (
        <div
          className="heatmap-tooltip font-mono"
          style={{
            top: `${tooltipPos.y + 12}px`,
            left: `${tooltipPos.x + 12}px`,
          }}
        >
          <div className="tooltip-header">
            <strong>{hoveredZone.department}</strong> // {hoveredZone.location}
          </div>
          <div className="tooltip-body">
            <span>Score: <strong>{hoveredZone.risk_score.toFixed(1)}</strong></span> &bull;{' '}
            <span>{hoveredZone.report_count} report{hoveredZone.report_count !== 1 ? 's' : ''}</span> &bull;{' '}
            <span className={`tooltip-level ${getRiskColor(hoveredZone.risk_level)}`}>
              {hoveredZone.risk_level}
            </span>
          </div>
        </div>
      )}

      {/* Expanded Zone Detail Drawer / Card */}
      {selectedZone && (
        <div className="zone-detail-card">
          <div className="zone-detail-header">
            <div>
              <span className="zone-tag font-mono">SELECTED ZONE DETAIL</span>
              <h4>{selectedZone.department} &mdash; {selectedZone.location}</h4>
            </div>
            <button className="btn-close" onClick={() => setSelectedZone(null)}>&times;</button>
          </div>
          <div className="zone-detail-grid font-mono">
            <div className="zone-stat">
              <span className="stat-lbl">TIME-DECAY RISK SCORE</span>
              <span className="stat-val font-mono">{selectedZone.risk_score.toFixed(2)}</span>
            </div>
            <div className="zone-stat">
              <span className="stat-lbl">ASSIGNED THREAT TIER</span>
              <span className={`stat-val ${getRiskColor(selectedZone.risk_level)}`}>
                {selectedZone.risk_level}
              </span>
            </div>
            <div className="zone-stat">
              <span className="stat-lbl">OBSERVATION COUNT</span>
              <span className="stat-val">{selectedZone.report_count} reports filed</span>
            </div>
            <div className="zone-stat">
              <span className="stat-lbl">OPERATIONAL STATUS</span>
              <span className="stat-val">
                {selectedZone.risk_level === 'High Risk'
                  ? 'CRITICAL PRECURSOR CLUSTER — IMMEDIATE MITIGATION REQUIRED'
                  : selectedZone.risk_level === 'Medium Risk'
                  ? 'ACTIVE HAZARD POTENTIAL — ELEVATE SHIFT INSPECTIONS'
                  : 'NORMAL STABILITY — STANDARD PROTOCOL'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RiskHeatmap;
