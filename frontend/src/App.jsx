import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import api from './api/api';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import Dashboard from './pages/Dashboard';
import ReportForm from './pages/ReportForm';
import ReportsList from './pages/ReportsList';
import Login from './pages/Login';
import Register from './pages/Register';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function AppLayout({ children, alertCount }) {
  return (
    <div className="app-shell">
      <ErrorBoundary fallbackMessage="Sidebar navigation module encountered an error.">
        <Sidebar alertCount={alertCount} />
      </ErrorBoundary>
      <div className="main-wrapper">
        <TopBar alertCount={alertCount} />
        <main className="content-area">
          <ErrorBoundary fallbackMessage="The operations view encountered a critical rendering exception.">
            {children}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

function AppRoutes() {
  const [alertCount, setAlertCount] = useState(0);
  const { token } = useAuth();

  const checkAlertCount = async () => {
    try {
      const res = await api.get('/alerts');
      if (Array.isArray(res.data)) {
        setAlertCount(res.data.length);
      }
    } catch (err) {
      // Do not log excessively, let page interceptor handle
    }
  };

  // Only poll for alerts once logged in
  useEffect(() => {
    if (!token) return;
    checkAlertCount();
    const interval = setInterval(checkAlertCount, 30000);
    return () => clearInterval(interval);
  }, [token]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout alertCount={alertCount}>
              <Dashboard />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/report"
        element={
          <ProtectedRoute>
            <AppLayout alertCount={alertCount}>
              <ReportForm />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <AppLayout alertCount={alertCount}>
              <ReportsList />
            </AppLayout>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
