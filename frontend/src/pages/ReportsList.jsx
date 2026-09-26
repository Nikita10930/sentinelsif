import React, { useState, useEffect } from 'react';
import api from '../api/api';

const HIGH_RISK_THRESHOLD = 8.0;
const MEDIUM_RISK_THRESHOLD = 4.0;

function riskColor(score) {
  if (score >= HIGH_RISK_THRESHOLD) return 'var(--red-critical)';
  if (score >= MEDIUM_RISK_THRESHOLD) return 'var(--amber-warning)';
  return 'var(--green-safe)';
}

function severityBadgeClass(severity) {
  if (!severity) return 'badge-sev-low';
  const s = severity.toLowerCase();
  if (s === 'high') return 'badge-sev-high';
  if (s === 'medium') return 'badge-sev-med';
  return 'badge-sev-low';
}

// Backend response mein ID field ka naam confirm nahi tha (id / report_id / reportId
// ho sakta hai) — isliye fallback chain use kar rahe hain taaki jo bhi ho, pick ho jaaye.
function getReportId(report) {
  return report.id ?? report.report_id ?? report.reportId;
}

export default function ReportsList() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // row-level UI state
  const [editingId, setEditingId] = useState(null);
  const [editDraft, setEditDraft] = useState({ department: '', location: '', description: '' });
  const [savingId, setSavingId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [rowError, setRowError] = useState({ id: null, message: '' });

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/reports');
      setReports(Array.isArray(res.data) ? res.data : []);
    } catch (err) {
      setError('Reports load nahi ho paaye. Backend chal raha hai ki check karo.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const startEdit = (report) => {
    setConfirmDeleteId(null);
    setEditingId(getReportId(report));
    setEditDraft({
      department: report.department || '',
      location: report.location || '',
      description: report.description || '',
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setRowError({ id: null, message: '' });
  };

  const saveEdit = async (id) => {
    setSavingId(id);
    setRowError({ id: null, message: '' });
    try {
      const res = await api.put(`/reports/${id}`, editDraft);
      setReports((prev) => prev.map((r) => (getReportId(r) === id ? res.data : r)));
      setEditingId(null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      let msg = 'Update fail ho gaya.';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((e) => e.msg || JSON.stringify(e)).join('; ');
      }
      setRowError({ id, message: msg });
    } finally {
      setSavingId(null);
    }
  };

  const confirmDelete = (id) => {
    setEditingId(null);
    setConfirmDeleteId(id);
  };

  const cancelDelete = () => setConfirmDeleteId(null);

  const doDelete = async (id) => {
    setDeletingId(id);
    try {
      await api.delete(`/reports/${id}`);
      setReports((prev) => prev.filter((r) => getReportId(r) !== id));
      setConfirmDeleteId(null);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'string' ? detail : 'Delete fail ho gaya.';
      setRowError({ id, message: msg });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <span className="panel-indicator cyan-pulse" />
          <h3>ALL REPORTS</h3>
        </div>
        <span className="panel-sub-tag">{reports.length} RECORDS</span>
      </div>

      {error && (
        <div className="network-error-banner">
          <div className="error-banner-content">
            <span>⚠</span>
            <span>{error}</span>
          </div>
          <button className="btn-retry" onClick={fetchReports}>RETRY</button>
        </div>
      )}

      {loading ? (
        <div className="empty-panel-state">
          <div className="empty-title">LOADING...</div>
        </div>
      ) : reports.length === 0 && !error ? (
        <div className="empty-panel-state">
          <div className="empty-icon">📋</div>
          <div className="empty-title">NO REPORTS FOUND</div>
          <div className="empty-sub">Ab tak koi hazard report submit nahi hua hai.</div>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                {['ID', 'Department', 'Location', 'Description', 'Hazard', 'Severity', 'Risk Score', 'Actions'].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: 'left',
                      padding: '10px 8px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '10px',
                      letterSpacing: '0.5px',
                      color: 'var(--text-muted)',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => {
                const rid = getReportId(r);
                const isEditing = editingId === rid;
                const isConfirmingDelete = confirmDeleteId === rid;
                const hasRowError = rowError.id === rid;

                return (
                  <tr
                    key={rid}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      backgroundColor: isEditing ? 'var(--bg-card)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '10px 8px', color: 'var(--text-muted)' }}>{rid}</td>

                    <td style={{ padding: '10px 8px' }}>
                      {isEditing ? (
                        <input
                          className="form-input"
                          style={{ width: '110px', padding: '6px 8px' }}
                          value={editDraft.department}
                          onChange={(e) => setEditDraft({ ...editDraft, department: e.target.value })}
                        />
                      ) : (
                        <span style={{ color: 'var(--text-secondary)' }}>{r.department}</span>
                      )}
                    </td>

                    <td style={{ padding: '10px 8px' }}>
                      {isEditing ? (
                        <input
                          className="form-input"
                          style={{ width: '110px', padding: '6px 8px' }}
                          value={editDraft.location}
                          onChange={(e) => setEditDraft({ ...editDraft, location: e.target.value })}
                        />
                      ) : (
                        <span style={{ color: 'var(--text-secondary)' }}>{r.location}</span>
                      )}
                    </td>

                    <td style={{ padding: '10px 8px', minWidth: '220px' }}>
                      {isEditing ? (
                        <textarea
                          className="form-textarea"
                          style={{ width: '100%', minHeight: '60px', padding: '6px 8px' }}
                          value={editDraft.description}
                          onChange={(e) => setEditDraft({ ...editDraft, description: e.target.value })}
                        />
                      ) : (
                        <span
                          style={{
                            color: 'var(--text-primary)',
                            display: 'block',
                            maxWidth: '320px',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                          title={r.description}
                        >
                          {r.description}
                        </span>
                      )}
                    </td>

                    <td style={{ padding: '10px 8px', color: 'var(--text-secondary)' }}>{r.hazard_type}</td>

                    <td style={{ padding: '10px 8px' }}>
                      <span className={`severity-badge ${severityBadgeClass(r.severity)}`}>
                        {r.severity}
                      </span>
                    </td>

                    <td style={{ padding: '10px 8px' }}>
                      <span style={{ fontWeight: 700, color: riskColor(r.risk_score) }}>
                        {Number(r.risk_score).toFixed(1)}
                      </span>
                    </td>

                    <td style={{ padding: '10px 8px', whiteSpace: 'nowrap' }}>
                      {isEditing ? (
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            className="btn-primary"
                            style={{ width: 'auto', padding: '6px 12px' }}
                            disabled={savingId === rid}
                            onClick={() => saveEdit(rid)}
                          >
                            {savingId === rid ? <span className="button-spinner" /> : 'SAVE'}
                          </button>
                          <button className="btn-secondary" onClick={cancelEdit}>CANCEL</button>
                        </div>
                      ) : isConfirmingDelete ? (
                        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                          <span style={{ fontSize: '11px', color: 'var(--red-critical)' }}>Sure?</span>
                          <button
                            className="btn-retry"
                            disabled={deletingId === rid}
                            onClick={() => doDelete(rid)}
                          >
                            {deletingId === rid ? '...' : 'YES'}
                          </button>
                          <button className="btn-secondary" onClick={cancelDelete}>NO</button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button className="btn-secondary" onClick={() => startEdit(r)}>EDIT</button>
                          <button
                            className="btn-secondary"
                            style={{ borderColor: 'var(--red-critical)', color: 'var(--red-critical)' }}
                            onClick={() => confirmDelete(rid)}
                          >
                            DELETE
                          </button>
                        </div>
                      )}
                      {hasRowError && (
                        <div style={{ color: 'var(--red-critical)', fontSize: '10px', marginTop: '4px' }}>
                          {rowError.message}
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}