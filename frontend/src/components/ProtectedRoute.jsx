import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children }) {
  const { user, token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div
        className="empty-panel-state font-mono"
        style={{ margin: '80px auto', maxWidth: '400px' }}
      >
        <div className="empty-title">AUTHENTICATING...</div>
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;