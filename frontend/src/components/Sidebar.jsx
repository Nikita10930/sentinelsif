import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Sidebar({ alertCount = 0 }) {
    const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  return (
    <aside className="sidebar">
      {/* Top Logo / Wordmark */}
      <div className="sidebar-brand">
        <div className="brand-logo-icon">
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#22D3EE"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="M12 8v4" />
            <path d="M12 16h.01" />
          </svg>
        </div>
        <div className="brand-text">
          <h1 className="brand-name">Sentinel<span>SIF</span></h1>
          <span className="brand-tag">OPS // COMMAND</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="sidebar-nav">
        <NavLink
          to="/"
          end
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
          <span>Dashboard</span>
          {alertCount > 0 && (
            <span className="sidebar-alert-badge pulse-red">
              {alertCount}
            </span>
          )}
        </NavLink>

        <NavLink
          to="/report"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="12" y1="18" x2="12" y2="12" />
            <line x1="9" y1="15" x2="15" y2="15" />
          </svg>
          <span>Submit Report</span>
        </NavLink>

                <NavLink
          to="/reports"
          className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="8" y1="6" x2="21" y2="6" />
            <line x1="8" y1="12" x2="21" y2="12" />
            <line x1="8" y1="18" x2="21" y2="18" />
            <line x1="3" y1="6" x2="3.01" y2="6" />
            <line x1="3" y1="12" x2="3.01" y2="12" />
            <line x1="3" y1="18" x2="3.01" y2="18" />
          </svg>
          <span>All Reports</span>
        </NavLink>
      </nav>

      {/* Telemetry / Live Status Footer */}
      <div className="sidebar-footer">
                {user && (
          <div
            className="font-mono"
            style={{
              padding: '10px 12px',
              marginBottom: '10px',
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {user.name}
            </div>
            <div style={{ fontSize: '10px', color: 'var(--cyan-primary)', letterSpacing: '0.5px', marginBottom: '8px' }}>
              {user.role.replace('_', ' ').toUpperCase()}
            </div>
            <button
              onClick={handleLogout}
              className="btn-secondary"
              style={{ width: '100%', fontSize: '10px', padding: '6px' }}
            >
              LOGOUT
            </button>
          </div>
        )}
        <div className="status-indicator">
          <span className="status-dot green-pulse"></span>
          <div className="status-meta">
            <span className="status-title">SYSTEM ONLINE</span>
            <span className="status-sub">SCADA PRECURSOR ENGINE</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
