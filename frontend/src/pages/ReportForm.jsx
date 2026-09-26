import React, { useState, useEffect, useRef } from 'react';
import api from '../api/api';
import ClassificationPreview from '../components/ClassificationPreview';
import ErrorBoundary from '../components/ErrorBoundary';

const DEPARTMENTS = [
  'Drilling',
  'Electrical',
  'Refining',
  'Warehouse',
  'Control Room',
  'Pipeline Maintenance',
  'Offshore Platform',
  'Logistics',
];

const LOCATIONS = [
  'Platform Alpha',
  'Maintenance Shed',
  'Boiler Room',
  'Pump House',
  'Rig 4',
  'Compressor Station',
  'Storage Yard',
  'Tank Farm 3',
  'Generator House',
  'Walkway Level 2',
];

function ReportForm() {
  const todayStr = new Date().toISOString().split('T')[0];

  const [formData, setFormData] = useState({
    department: '',
    location: '',
    description: '',
    date: todayStr,
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);
  const [networkError, setNetworkError] = useState(null);

  // Live Classification Preview state
  const [prediction, setPrediction] = useState(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const debounceTimerRef = useRef(null);

  // Debounced 800ms real-time classification as user types
  useEffect(() => {
    const text = formData.description.trim();

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    if (text.length < 5) {
      setPrediction(null);
      setIsClassifying(false);
      return;
    }

    setIsClassifying(true);

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const response = await api.post('/classify', { description: text });
        setPrediction(response.data);
      } catch (err) {
        console.error('[Live Classification Error]:', err);
        // Do not crash UI, keep prediction null or last valid
      } finally {
        setIsClassifying(false);
      }
    }, 800);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [formData.description]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear field-specific error upon editing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.department) {
      newErrors.department = 'Operational department selection is mandatory.';
    }
    if (!formData.location) {
      newErrors.location = 'Specific facility location is mandatory.';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Incident observation description is mandatory.';
    } else if (formData.description.trim().length < 5) {
      newErrors.description = 'Observation description must be at least 5 characters long.';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitResult(null);
    setNetworkError(null);

    if (!validate()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await api.post('/upload-report', {
        department: formData.department,
        location: formData.location,
        description: formData.description.trim(),
        date: formData.date || todayStr,
      });

      setSubmitResult(response.data);
      // Reset description while preserving department/location for fast consecutive reports
      setFormData((prev) => ({
        ...prev,
        description: '',
      }));
      setPrediction(null);
    } catch (err) {
      console.error('[Submit Report Error]:', err);
      const errMsg =
        err.response?.data?.detail ||
        'Unable to persist safety report to server. Check backend connectivity.';
      setNetworkError(errMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="report-form-page">
      <div className="report-page-grid">
        {/* Left Column: Form Panel */}
        <div className="form-column">
          <div className="panel form-panel">
            <div className="panel-header">
              <div className="panel-title-wrap">
                <span className="panel-indicator cyan-dot"></span>
                <h3>INGEST SAFETY OBSERVATION // REPORT TRANSMISSION</h3>
              </div>
              <span className="panel-sub-tag font-mono">FORM: SIF-INGEST-01</span>
            </div>

            {/* Success / Duplicate Notification Banners */}
            {submitResult && (
              <div className="submit-alert success-alert font-mono">
                <div className="submit-alert-top">
                  <span className="alert-icon">✅</span>
                  <div>
                    <strong>INCIDENT INGESTED SUCCESSFULLY // REPORT #{submitResult.report_id}</strong>
                    <p className="alert-details">
                      Hazard: <strong>{submitResult.hazard_type}</strong> &bull; Severity:{' '}
                      <strong>{submitResult.severity}</strong> &bull; Decayed Risk:{' '}
                      <strong>{submitResult.risk_score?.toFixed(1)}</strong>
                    </p>
                  </div>
                </div>

                {/* Duplicate Detection Warning Banner */}
                {submitResult.possible_duplicate_of && (
                  <div className="duplicate-warning-box">
                    <span className="dup-icon">⚠️</span>
                    <span>
                      <strong>DUPLICATE DETECTED:</strong> This description matches an incident report
                      filed within the last 7 days (Report #{submitResult.possible_duplicate_of}).
                      Report has been saved and flagged for supervisor review.
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Error Notification Banner */}
            {networkError && (
              <div className="submit-alert error-alert font-mono">
                <span className="alert-icon">❌</span>
                <div>
                  <strong>TRANSMISSION FAILED:</strong> {networkError}
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} noValidate className="safety-form">
              {/* Department & Location Row */}
              <div className="form-row-2">
                <div className="form-group">
                  <label htmlFor="department" className="form-label font-mono">
                    FACILITY DEPARTMENT <span className="req">*</span>
                  </label>
                  <select
                    id="department"
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    className={`form-input font-mono ${errors.department ? 'input-error' : ''}`}
                  >
                    <option value="">-- SELECT DEPARTMENT --</option>
                    {DEPARTMENTS.map((dept) => (
                      <option key={dept} value={dept}>
                        {dept}
                      </option>
                    ))}
                  </select>
                  {errors.department && (
                    <span className="error-text font-mono">{errors.department}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="location" className="form-label font-mono">
                    SITE LOCATION <span className="req">*</span>
                  </label>
                  <select
                    id="location"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    className={`form-input font-mono ${errors.location ? 'input-error' : ''}`}
                  >
                    <option value="">-- SELECT LOCATION --</option>
                    {LOCATIONS.map((loc) => (
                      <option key={loc} value={loc}>
                        {loc}
                      </option>
                    ))}
                  </select>
                  {errors.location && (
                    <span className="error-text font-mono">{errors.location}</span>
                  )}
                </div>
              </div>

              {/* Date Input */}
              <div className="form-group">
                <label htmlFor="date" className="form-label font-mono">
                  OBSERVATION DATE
                </label>
                <input
                  type="date"
                  id="date"
                  name="date"
                  value={formData.date}
                  onChange={handleChange}
                  className="form-input font-mono"
                />
              </div>

              {/* Description Input */}
              <div className="form-group">
                <div className="label-row">
                  <label htmlFor="description" className="form-label font-mono">
                    INCIDENT / HAZARD DESCRIPTION <span className="req">*</span>
                  </label>
                  <span className="char-counter font-mono">
                    {formData.description.length} chars
                  </span>
                </div>
                <textarea
                  id="description"
                  name="description"
                  rows="5"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="e.g. Panel ke paas loose wire dikha aur sparking ho rahi thi near generator unit, koi bhi touch kar sakta tha..."
                  className={`form-textarea ${errors.description ? 'input-error' : ''}`}
                ></textarea>
                {errors.description ? (
                  <span className="error-text font-mono">{errors.description}</span>
                ) : (
                  <span className="form-hint font-mono">
                    Hinglish or English phrasing supported. Neural classifier activates at 5+ characters.
                  </span>
                )}
              </div>

              {/* Action Submit Button */}
              <div className="form-actions">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn-primary font-mono"
                >
                  {isSubmitting ? (
                    <>
                      <span className="button-spinner"></span>
                      TRANSMITTING REPORT...
                    </>
                  ) : (
                    'TRANSMIT SAFETY REPORT &rarr;'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Live NLP Inference Preview */}
        <div className="preview-column">
          <ErrorBoundary fallbackMessage="Real-time inference preview module encountered an error.">
            <ClassificationPreview
              prediction={prediction}
              isClassifying={isClassifying}
              charCount={formData.description.trim().length}
            />
          </ErrorBoundary>

          {/* Quick Guide Card */}
          <div className="panel guide-panel font-mono">
            <div className="panel-header">
              <span className="cyan-dot"></span>
              <h4>OPERATOR GUIDELINES</h4>
            </div>
            <ul className="guide-list">
              <li>
                <strong>Precursor Identification:</strong> SIF events stem from near-misses. Record subtle precursors before loss of life/limb occurs.
              </li>
              <li>
                <strong>Bilingual Natural Language:</strong> Feel free to include mixed vocabulary (e.g. <em>khula switchboard, phisal gaya, harness nahi tha</em>).
              </li>
              <li>
                <strong>Duplicate Suppression:</strong> Submitting identical observations within 7 days flags duplicate linkage automatically.
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReportForm;
