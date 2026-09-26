import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

function TopBar({ alertCount = 0, isLiveConnected = true }) {
  const location = useLocation();
  const [timeStr, setTimeStr] = useState('');
  const [dateStr, setDateStr] = useState('');

  // Live clock updating every second
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeFormatted = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
      const dateFormatted = now.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: '2-digit',
      });
      setTimeStr(timeFormatted);
      setDateStr(dateFormatted);
    };

    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'FACILITY OVERVIEW // REAL-TIME RISK TELEMETRY';
      case '/report':
        return 'INCIDENT INGESTION // NEW SAFETY OBSERVATION';
      case '/reports':
        return 'REPORT LEDGER // FULL INCIDENT ARCHIVE';
      default:
        return 'OPERATIONS CONSOLE';
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-title-area">
        <span className="terminal-prefix">&gt;</span>
        <h2 className="topbar-title">{getPageTitle()}</h2>
      </div>

      <div className="topbar-meta">
        {/* Active Alert Flag */}
        {alertCount > 0 ? (
          <div className="topbar-chip alert-chip pulse-red">
            <span className="chip-dot red-dot"></span>
            <span>{alertCount} CRITICAL ALERT{alertCount > 1 ? 'S' : ''}</span>
          </div>
        ) : (
          <div className="topbar-chip safe-chip">
            <span className="chip-dot green-dot"></span>
            <span>NO ACTIVE CRITICAL ALERTS</span>
          </div>
        )}

        {/* Live Ops Clock */}
        <div className="topbar-clock">
          <span className="clock-date">{dateStr}</span>
          <span className="clock-time">{timeStr}</span>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
