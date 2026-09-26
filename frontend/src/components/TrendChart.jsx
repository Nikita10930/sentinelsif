import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

const DEPT_COLORS = {
  Drilling: '#22D3EE',
  Electrical: '#F59E0B',
  Refining: '#EF4444',
  Warehouse: '#10B981',
  'Control Room': '#A855F7',
  'Pipeline Maintenance': '#3B82F6',
  'Offshore Platform': '#EC4899',
  Logistics: '#6366F1',
};

const DEFAULT_COLORS = ['#22D3EE', '#F59E0B', '#EF4444', '#10B981', '#A855F7', '#3B82F6'];

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="chart-tooltip font-mono">
        <div className="chart-tooltip-title">DATE: {label}</div>
        <div className="chart-tooltip-items">
          {payload.map((entry, index) => (
            <div key={`item-${index}`} className="chart-tooltip-item" style={{ color: entry.color }}>
              <span>{entry.name}:</span>
              <strong>{typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}</strong>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
}

function TrendChart({ chartData = [], departments = [] }) {
  const hasEnoughData = chartData && chartData.length >= 2;

  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <div className="panel-title-wrap">
          <span className="panel-indicator cyan-dot"></span>
          <h3>FACILITY SIF PRECURSOR TREND // RISK TRAJECTORY OVER TIME</h3>
        </div>
        <span className="panel-sub-tag font-mono">TIMELINE TELEMETRY</span>
      </div>

      {!hasEnoughData ? (
        <div className="empty-panel-state chart-empty">
          <div className="empty-icon">📈</div>
          <p className="empty-title">INSUFFICIENT HISTORICAL DATA POINTS</p>
          <p className="empty-sub">
            Timeline trajectory requires reports distributed across multiple dates. As operations teams submit new safety observations, comparative department trends will render here automatically.
          </p>
        </div>
      ) : (
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1B2330" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                fontFamily="JetBrains Mono, monospace"
              />
              <YAxis
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                fontFamily="JetBrains Mono, monospace"
                domain={[0, 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{
                  paddingTop: '12px',
                  fontSize: '11px',
                  fontFamily: 'JetBrains Mono, monospace',
                }}
              />
              {departments.map((dept, index) => (
                <Line
                  key={dept}
                  type="monotone"
                  dataKey={dept}
                  name={dept}
                  stroke={DEPT_COLORS[dept] || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 3, fill: DEPT_COLORS[dept] || DEFAULT_COLORS[index % DEFAULT_COLORS.length] }}
                  activeDot={{ r: 5 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default TrendChart;
