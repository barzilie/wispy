import React, { useState } from 'react';
import '../DnsTable/DnsTable.css';
import './PlaintextPanel.css';
import { formatTimestamp } from './PlaintextPanel.logic';

const PlaintextPanel = ({ plaintext = [], plaintextTotal = 0 }) => {
  const [expandedRow, setExpandedRow] = useState(null);

  const toggleExpand = (id) => {
    if (expandedRow === id) {
      setExpandedRow(null);
    } else {
      setExpandedRow(id);
    }
  };

  if (plaintext.length === 0) {
    return (
      <section className="section">
        <h2>⚠️ Plaintext Packet Hunting</h2>
        <p className="plaintext-empty">
          No plaintext HTTP or SMTP packets detected. The network segment appears secure.
        </p>
      </section>
    );
  }

  return (
    <section className="section">
      <h2>
        ⚠️ Plaintext Leaks Detected ({plaintextTotal || plaintext.length})
        {plaintextTotal > plaintext.length && (
          <span className="plaintext-count"> — showing {plaintext.length} recent</span>
        )}
      </h2>
      <div className="dns-table-container">
        <table className="dns-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Device</th>
              <th>Protocol</th>
              <th>Host / Server</th>
              <th>Method / Command</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {plaintext.map((row) => (
              <React.Fragment key={`plaintext-${row.id}`}>
                <tr className="plaintext-row-leak">
                  <td>{formatTimestamp(row.timestamp)}</td>
                  <td className="device-mac">{row.device_mac}</td>
                  <td>
                    <span className="plaintext-badge">{row.proto.toUpperCase()}</span>
                  </td>
                  <td className="domain" style={{ color: '#ff3333' }}>{row.host_or_server}</td>
                  <td className="plaintext-method">{row.method_or_command}</td>
                  <td>
                    <button 
                      onClick={() => toggleExpand(row.id)}
                      className="recommend-button" 
                      style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', minHeight: 'auto', margin: 0, textTransform: 'capitalize', letterSpacing: '1px' }}
                    >
                      {expandedRow === row.id ? 'Hide Body' : 'Inspect Body'}
                    </button>
                  </td>
                </tr>
                {expandedRow === row.id && (
                  <tr>
                    <td colSpan="6" style={{ backgroundColor: '#050505', padding: '1rem' }}>
                      <div style={{ color: '#ff6666', fontSize: '0.85rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                        [ RAW PACKET PAYLOAD BODY ]
                      </div>
                      <pre className="plaintext-payload-pre">
                        {row.body || 'No payload body captured.'}
                      </pre>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default PlaintextPanel;
