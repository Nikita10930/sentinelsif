import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../api/api';
import KpiCard from '../components/KpiCard';
import RiskHeatmap from '../components/RiskHeatmap';
import TrendChart from '../components/TrendChart';
import AlertsList from '../components/AlertsList';
import ErrorBoundary from '../components/ErrorBoundary';

function Dashboard() {
  const [riskSummary, setRiskSummary] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCountdown, setRetryCountdown] = useState(0);
  const [lastRefreshed, setLastRefreshed] = useState(null);

  const retryTimerRef = useRef(null);

  const fetchData = useCallback(async (isSilent = false) => {
    if (!isSilent) {
      setLoading(true);
    }
    setError(null);

    try {
      const [summaryRes, alertsRes, reportsRes] = await Promise.all([
        api.get('/risk-summary'),
        api.get('/alerts'),
        api.get('/reports'),
      ]);

      setRiskSummary(summaryRes.data || []);
      setAlerts(alertsRes.data || []);
      setReports(reportsRes.data || []);
      setLastRefreshed(new Date());
    } catch (err) {
      console.error('[Dashboard fetch error]:', err);
      setError('Unable to establish telemetry connection with backend server.');
      // Start 5s countdown for automatic retry
      setRetryCountdown(5);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchData(false);
  }, [fetchData]);

  // Silent 30s auto-refresh
  useEffect(() => {
    const autoRefresh = setInterval(() => {
      fetchData(true);
    }, 30000);

    return () => clearInterval(autoRefresh);
  }, [fetchData]);

  // Handle retry countdown
  useEffect(() => {
    if (retryCountdown <= 0) return;

    retryTimerRef.current = setTimeout(() => {
      if (retryCountdown === 1) {
        fetchData(false);
        setRetryCountdown(0);
      } else {
        setRetryCountdown((prev) => prev - 1);
      }
    }, 1000);

    return () => clearTimeout(retryTimerRef.current);
  }, [retryCountdown, fetchData]);

  // KPI Calculations
  const totalReports = riskSummary.reduce((acc, curr) => acc + (curr.report_count || 0), 0);
  const highRiskCount = alerts.length;
    // Active Incidents = reports filed in the last 7 days (distinct from the
  // all-time cumulative total shown in TOTAL OBSERVATIONS above)
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const reportsThisWeek = reports.filter((r) => {
    if (!r.date) return false;
    return new Date(r.date) >= sevenDaysAgo;
  }).length;
  const avgRiskScore =
    riskSummary.length > 0
      ? riskSummary.reduce((acc, curr) => acc + (curr.risk_score || 0), 0) / riskSummary.length
      : 0;

  // Build Trend Chart Data directly from raw reports (their actual observation
  // `date` field, as submitted via ReportForm) — NOT from /alerts, since alerts
  // only contains high-risk (score >= 8.0) clusters and is usually empty/sparse
  // during normal testing, which meant the trend chart never had real dates to plot.
  const departments = Array.from(new Set(reports.map((r) => r.department)));

  const timelineMap = {};
  reports.forEach((r) => {
    const d = r.date;
    if (!d) return;
    if (!timelineMap[d]) {
      timelineMap[d] = { date: d };
    }
    // risk_score is a cumulative running snapshot per department/location at
    // the time each report was filed — keep the highest value seen for that
    // department on that date so the line reflects the latest known state.
    const existing = timelineMap[d][r.department];
    timelineMap[d][r.department] =
      existing !== undefined ? Math.max(existing, r.risk_score) : r.risk_score;
  });

  const chartData = Object.values(timelineMap).sort((a, b) => (a.date > b.date ? 1 : -1));

  return (
    <div className="dashboard-page">
      {/* Network Error Calm Recovery Banner */}
      {error && (
        <div className="network-error-banner font-mono">
          <div className="error-banner-content">
            <span className="error-indicator red-dot pulse-red"></span>
            <span>
              <strong>TELEMETRY OFFLINE:</strong> {error}{' '}
              {retryCountdown > 0 && `Auto-reconnecting in ${retryCountdown}s...`}
            </span>
          </div>
          <button className="btn-retry" onClick={() => fetchData(false)}>
            Force Reconnect
          </button>
        </div>
      )}

      {/* KPI Stats Row */}
      <section className="kpi-row">
        <KpiCard
          title="TOTAL OBSERVATIONS"
          value={totalReports}
          subtitle="Cumulative safety reports"
          icon="📋"
          status="cyan"
        />
        <KpiCard
          title="HIGH RISK ZONES"
          value={highRiskCount}
          subtitle="Clusters exceeding 8.0 score"
          icon="🚨"
          status={highRiskCount > 0 ? 'danger' : 'success'}
        />
        <KpiCard
          title="ACTIVE INCIDENTS"
          value={reportsThisWeek}
          subtitle="Filed in last 7 days"
          icon="⚡"
          status="warning"
        />
        <KpiCard
          title="AVERAGE RISK INDEX"
          value={avgRiskScore}
          subtitle="Decayed facility aggregate"
          icon="📊"
          status={avgRiskScore > 8 ? 'danger' : avgRiskScore > 4 ? 'warning' : 'cyan'}
          isFloat
        />
      </section>

      {/* Main Grid: Heatmap + Alerts */}
      <div className="dashboard-main-grid">
        {/* Risk Heatmap (Left Column) */}
        <div className="grid-left-col">
          <ErrorBoundary fallbackMessage="Risk Heatmap telemetry module encountered an error.">
            <RiskHeatmap data={riskSummary} />
          </ErrorBoundary>

          {/* Trend Line Chart */}
          <ErrorBoundary fallbackMessage="Trend visualization module encountered an error.">
            <TrendChart chartData={chartData} departments={departments} />
          </ErrorBoundary>
        </div>

        {/* Live Alerts Panel (Right Column) */}
        <div className="grid-right-col">
          <ErrorBoundary fallbackMessage="Alerts telemetry feed encountered an error.">
            <AlertsList alerts={alerts} />
          </ErrorBoundary>

          {/* Quick System Telemetry Card */}
          <div className="panel telemetry-info-panel font-mono">
            <div className="telemetry-info-header">
              <span className="cyan-dot"></span>
              <h4>MONITORING ENGINE STATUS</h4>
            </div>
            <div className="telemetry-info-body">
              <div className="info-row">
                <span>POLLING INTERVAL:</span>
                <strong>30s (AUTO-SYNC)</strong>
              </div>
              <div className="info-row">
                <span>TIME-DECAY RATE (&lambda;):</span>
                <strong>0.05 / DAY</strong>
              </div>
              <div className="info-row">
                <span>ML NLP INFERENCE:</span>
                <strong>MULTINOMIAL NB + TF-IDF</strong>
              </div>
              <div className="info-row">
                <span>LAST TELEMETRY SYNC:</span>
                <strong>{lastRefreshed ? lastRefreshed.toLocaleTimeString() : 'INITIALIZING'}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;