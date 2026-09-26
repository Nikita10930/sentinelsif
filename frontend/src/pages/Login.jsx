import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
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
      await login(formData.email.trim(), formData.password);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Login failed. Check your credentials.');
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
            <h3>SENTINELSIF // OPERATOR LOGIN</h3>
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
            <label htmlFor="email" className="form-label font-mono">EMAIL</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="form-input font-mono"
              placeholder="you@facility.com"
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
              className="form-input font-mono"
              placeholder="••••••••"
            />
          </div>

          <div className="form-actions">
            <button type="submit" disabled={isSubmitting} className="btn-primary font-mono">
              {isSubmitting ? (
                <>
                  <span className="button-spinner"></span>
                  AUTHENTICATING...
                </>
              ) : (
                'LOG IN →'
              )}
            </button>
          </div>
        </form>

        <p
          className="font-mono"
          style={{ textAlign: 'center', marginTop: '16px', fontSize: '11px', color: 'var(--text-muted)' }}
        >
          No account? <Link to="/register" style={{ color: 'var(--cyan-primary)' }}>Register here</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;