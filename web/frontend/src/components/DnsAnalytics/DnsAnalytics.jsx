import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
} from 'recharts';
import './DnsAnalytics.css';
import { buildQueriesPerMinute, buildTopDomains } from './DnsAnalytics.logic';

const axisStyle = { fill: '#00cc00', fontSize: 11, fontFamily: 'Courier New, monospace' };
const gridColor = 'rgba(0, 255, 0, 0.15)';

const DnsAnalytics = ({ dnsQueries }) => {
  const perMinute = useMemo(() => buildQueriesPerMinute(dnsQueries), [dnsQueries]);
  const topDomains = useMemo(() => buildTopDomains(dnsQueries, 14), [dnsQueries]);

  if (!dnsQueries.length) {
    return (
      <section className="section dns-analytics">
        <h2>📈 DNS activity</h2>
        <p className="dns-analytics-empty">No DNS rows yet — charts appear after queries are captured.</p>
      </section>
    );
  }

  return (
    <section className="section dns-analytics">
      <h2>📈 DNS activity</h2>
      <div className="dns-analytics-grid">
        <div className="dns-chart-panel">
          <h3>Queries over time (per minute)</h3>
          <div className="dns-chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={perMinute} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis dataKey="minute" tick={axisStyle} interval="preserveStartEnd" minTickGap={24} />
                <YAxis tick={axisStyle} allowDecimals={false} width={36} />
                <Tooltip
                  contentStyle={{
                    background: '#0a0a0a',
                    border: '1px solid #00ff00',
                    fontFamily: 'Courier New, monospace',
                    color: '#00ff00',
                  }}
                />
                <Line type="monotone" dataKey="queries" stroke="#00ff00" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="dns-chart-panel">
          <h3>Top queried domains</h3>
          <div className="dns-chart-wrap dns-bar-wrap">
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={topDomains}
                layout="vertical"
                margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} horizontal={false} />
                <XAxis type="number" tick={axisStyle} allowDecimals={false} />
                <YAxis
                  type="category"
                  dataKey="domain"
                  width={160}
                  tick={{ ...axisStyle, fontSize: 10 }}
                  interval={0}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0a0a0a',
                    border: '1px solid #00ff00',
                    fontFamily: 'Courier New, monospace',
                    color: '#00ff00',
                  }}
                />
                <Bar dataKey="count" fill="#00cc00" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </section>
  );
};

export default DnsAnalytics;
