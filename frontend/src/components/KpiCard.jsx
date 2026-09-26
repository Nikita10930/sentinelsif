import React, { useState, useEffect } from 'react';

function KpiCard({ title, value, unit = '', subtitle, icon, status = 'normal', isFloat = false }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    const target = typeof value === 'number' ? value : parseFloat(value) || 0;
    if (target === 0) {
      setDisplayValue(0);
      return;
    }

    const duration = 800; // ms
    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutCubic easing
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = target * ease;

      setDisplayValue(isFloat ? current.toFixed(1) : Math.round(current));

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setDisplayValue(isFloat ? target.toFixed(1) : target);
      }
    };

    requestAnimationFrame(animate);
  }, [value, isFloat]);

  const getStatusClass = () => {
    switch (status) {
      case 'danger':
        return 'kpi-danger';
      case 'warning':
        return 'kpi-warning';
      case 'success':
        return 'kpi-success';
      case 'cyan':
      default:
        return 'kpi-cyan';
    }
  };

  return (
    <div className={`kpi-card ${getStatusClass()}`}>
      <div className="kpi-card-header">
        <span className="kpi-title">{title}</span>
        {icon && <span className="kpi-icon">{icon}</span>}
      </div>
      <div className="kpi-value-row">
        <span className="kpi-value font-mono">{displayValue}</span>
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
      <div className="kpi-corner-accent"></div>
    </div>
  );
}

export default KpiCard;
