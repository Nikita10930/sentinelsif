import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ROLES = [
  { value: 'worker', label: 'Worker' },
  { value: 'safety_officer', label: 'Safety Officer' },
  { value: 'admin', label: 'Admin' },
];

function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'worker' });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register(formData.name.trim(), formData.email.trim(), formData.password, formData.role);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      let msg = 'Registration failed.';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((e) => e.msg || JSON.stringify(e)).join('; ');
      }
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-base)',
      }}
    >
      <div className="panel" style={{ width: '380px' }}>
        <div className="panel-header">
          <div className="panel-title-wrap">
            <span className="panel-indicator cyan-dot"></span>
            <h3>SENTINELSIF // NEW OPERATOR</h3>
          </div>
        </div>

        {error && (
          <div className="submit-alert error-alert font-mono" style={{ marginBottom: '16px' }}>
            <span className="alert-icon">❌</span>
            <div>{error}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="name" className="form-label font-mono">FULL NAME</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="form-input font-mono"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email" className="form-label font-mono">EMAIL</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-input font-mono"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label font-mono">PASSWORD</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={6}
              className="form-input font-mono"
            />
            <span className="form-hint font-mono">Minimum 6 characters.</span>
          </div>

          <div className="form-group">
            <label htmlFor="role" className="form-label font-mono">ROLE</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="form-input font-mono"
            >
              {ROLES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div className="form-actions">
            <button type="submit" disabled={isSubmitting} className="btn-primary font-mono">
              {isSubmitting ? (
                <>
                  <span className="button-spinner"></span>
                  REGISTERING...
                </>
              ) : (
                'REGISTER →'
              )}
            </button>
          </div>
        </form>

        <p
          className="font-mono"
          style={{ textAlign: 'center', marginTop: '16px', fontSize: '11px', color: 'var(--text-muted)' }}
        >
          Already have an account? <Link to="/login" style={{ color: 'var(--cyan-primary)' }}>Log in</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;