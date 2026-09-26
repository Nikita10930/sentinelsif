import React from 'react';

const HAZARD_ICONS = {
  Electrical: '⚡',
  Fire: '🔥',
  Fall: '🪜',
  Machinery: '⚙️',
  Chemical: '🧪',
};

function ClassificationPreview({ prediction, isClassifying, charCount = 0 }) {
  const getSeverityClass = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return 'badge-sev-high';
      case 'medium':
        return 'badge-sev-med';
      case 'low':
      default:
        return 'badge-sev-low';
    }
  };

  const confidencePct = prediction
    ? Math.round(prediction.hazard_confidence * 100)
    : 0;

  const severityConfidencePct = prediction
    ? Math.round(prediction.severity_confidence * 100)
    : 0;

  const icon = prediction?.hazard_type ? HAZARD_ICONS[prediction.hazard_type] || '⚠️' : '🛡️';

  return (
    <div className="panel preview-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <span className={`panel-indicator ${isClassifying ? 'cyan-pulse' : 'cyan-dot'}`}></span>
          <h3>NEURAL SIF INFERENCE // LIVE PRECURSOR TELEMETRY</h3>
        </div>
        {isClassifying && (
          <span className="classifying-spinner font-mono">CLASSIFYING...</span>
        )}
      </div>

      {charCount < 5 ? (
        <div className="preview-empty-state">
          <div className="radar-animation">
            <div className="radar-circle circle-1"></div>
            <div className="radar-circle circle-2"></div>
            <div className="radar-sweep"></div>
          </div>
          <p className="preview-prompt-title">AWAITING INCIDENT OBSERVATION</p>
          <p className="preview-prompt-sub">
            Input at least 5 characters in the description field to trigger real-time NLP precursor classification.
          </p>
        </div>
      ) : !prediction && isClassifying ? (
        <div className="preview-loading-state font-mono">
          <div className="telemetry-shimmer"></div>
          <p>PROCESSING NLP TOKENS &bull; TF-IDF VECTORIZATION...</p>
        </div>
      ) : prediction ? (
        <div className="preview-content">
          {/* Main Hazard Card */}
          <div className="preview-main-card">
            <div className="preview-hazard-header">
              <span className="preview-icon">{icon}</span>
              <div className="preview-hazard-title">
                <span className="preview-sub font-mono">PRECURSOR CATEGORY</span>
                <h4>{prediction.hazard_type}</h4>
              </div>
            </div>

            {/* Visual Confidence Bar */}
            <div className="confidence-block font-mono">
              <div className="confidence-label-row">
                <span>MODEL CONFIDENCE</span>
                <strong>{confidencePct}%</strong>
              </div>
              <div className="confidence-track">
                <div
                  className="confidence-fill"
                  style={{ width: `${Math.min(confidencePct, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Explainability: top driving keywords */}
            {prediction.top_keywords && prediction.top_keywords.length > 0 && (
              <div className="keyword-chips-row" style={{ marginTop: '12px' }}>
                <span
                  className="metric-box-title font-mono"
                  style={{ display: 'block', marginBottom: '6px' }}
                >
                  TOP DRIVING KEYWORDS
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {prediction.top_keywords.map((word) => (
                    <span
                      key={word}
                      className="font-mono"
                      style={{
                        fontSize: '10px',
                        fontWeight: 600,
                        padding: '3px 8px',
                        borderRadius: '2px',
                        backgroundColor: 'rgba(34, 211, 238, 0.08)',
                        border: '1px solid rgba(34, 211, 238, 0.3)',
                        color: 'var(--cyan-primary)',
                      }}
                    >
                      {word}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Severity & Metrics Row */}
          <div className="preview-metrics-grid font-mono">
            <div className="preview-metric-box">
              <span className="metric-box-title">PREDICTED SEVERITY</span>
              <span className={`severity-badge ${getSeverityClass(prediction.severity)}`}>
                {prediction.severity?.toUpperCase() || 'UNKNOWN'}
              </span>
              <span className="metric-box-sub">
                Conf: <strong>{severityConfidencePct}%</strong>
              </span>
            </div>

            <div className="preview-metric-box">
              <span className="metric-box-title">INFERENCE PIPELINE</span>
              {prediction.used_fallback ? (
                <div className="fallback-tag warning font-mono">
                  <span className="fallback-dot amber-dot"></span>
                  <span>KEYWORD FALLBACK</span>
                </div>
              ) : (
                <div className="fallback-tag ml-direct font-mono">
                  <span className="fallback-dot cyan-dot"></span>
                  <span>MULTINOMIAL NB</span>
                </div>
              )}
              <span className="metric-box-sub">
                {prediction.used_fallback ? 'Confidence < 0.60' : 'Direct Model Output'}
              </span>
            </div>
          </div>

          {/* Fallback Notice Banner if triggered */}
          {prediction.used_fallback && (
            <div className="fallback-explanation font-mono">
              <span className="notice-icon">ℹ️</span>
              <span>
                <strong>Safety Rule Active:</strong> ML confidence was under 60%. Keyword fallback was utilized for deterministic fail-safe classification.
              </span>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

export default ClassificationPreview;