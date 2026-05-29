import React from 'react';
import '../DnsTable/DnsTable.css';
import './FlowAnalytics.css';
import { formatBytes, getHostBadgeClass, formatTimestamp } from './FlowAnalytics.logic';

const FlowAnalytics = ({ flows = [], flowsTotal = 0 }) => {
  if (flows.length === 0) {
    return (
      <section className="section">
        <h2>📊 Session Reconnaissance</h2>
        <p className="flow-analytics-empty">
          No flow sessions detected yet. Waiting for client network activity...
        </p>
      </section>
    );
  }

  return (
    <section className="section">
      <h2>
        📊 Session Reconnaissance (Flows)
        {flowsTotal > flows.length && (
          <span className="flow-analytics-count"> — showing {flows.length} of {flowsTotal}</span>
        )}
      </h2>
      <div className="dns-table-container" style={{ maxHeight: '400px' }}>
        <table className="dns-table">
          <thead>
            <tr>
              <th>Last Active</th>
              <th>Device</th>
              <th>Proto</th>
              <th>Source IP</th>
              <th>Destination Host / IP</th>
              <th>Port</th>
              <th>Label</th>
              <th>Resolution</th>
              <th>Packets</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {flows.map((flow) => {
              const displayHost = flow.dst_host && flow.dst_host !== 'unknown' ? flow.dst_host : flow.dst_ip;
              const hasCorrelatedHost = flow.dst_host && flow.dst_host !== 'unknown';
              return (
                <tr key={`flow-${flow.id}`}>
                  <td>{formatTimestamp(flow.last_seen)}</td>
                  <td className="device-mac">{flow.device_mac}</td>
                  <td>{flow.proto}</td>
                  <td>{flow.src_ip}</td>
                  <td className="domain" style={{ color: hasCorrelatedHost ? '#00ff00' : '#888888' }}>
                    {displayHost}
                  </td>
                  <td>{flow.dst_port}</td>
                  <td>{flow.service_label || 'UNKNOWN'}</td>
                  <td>
                    <span className={getHostBadgeClass(flow.host_source)}>
                      {(flow.host_source || 'unknown').toUpperCase()}
                    </span>
                  </td>
                  <td>{flow.packet_count}</td>
                  <td className="flow-bytes">{formatBytes(flow.byte_count)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default FlowAnalytics;
