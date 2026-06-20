import React from 'react';
import '../DnsTable/DnsTable.css';
import './TelemetryTables.css';
import { formatTimestamp } from '../DnsTable/DnsTable.logic';

const TelemetryTables = ({ tlsSni = [], ja3 = [], mdns = [] }) => {
  const hasAny = tlsSni.length > 0 || ja3.length > 0 || mdns.length > 0;

  if (!hasAny) {
    return (
      <section className="section">
        <h2>🔐 TLS / JA3 / mDNS</h2>
        <p className="telemetry-empty">
          No TLS ClientHello, JA3, or mDNS rows yet. Run the sniffer against live traffic on the rogue AP.
        </p>
      </section>
    );
  }

  return (
    <section className="section telemetry-tables">
      <h2>🔐 TLS SNI · JA3 · mDNS</h2>
      
      {/* --- LINE 1: TLS SNI & JA3 --- */}
      <div className="telemetry-row">
        <div className="telemetry-col">
          <h3 className="telemetry-subtitle">TLS SNI ({tlsSni.length})</h3>
          <div className="dns-table-container telemetry-scroll">
            <table className="dns-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Device</th>
                  <th>SNI</th>
                </tr>
              </thead>
              <tbody>
                {tlsSni.map((row) => (
                  <tr key={`tls-${row.id}`}>
                    <td>{formatTimestamp(row.timestamp)}</td>
                    <td className="device-mac">{row.device_mac}</td>
                    <td className="domain">{row.sni}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="telemetry-col">
          <h3 className="telemetry-subtitle">JA3 ({ja3.length})</h3>
          <div className="dns-table-container telemetry-scroll">
            <table className="dns-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Device</th>
                  <th>Hash</th>
                </tr>
              </thead>
              <tbody>
                {ja3.map((row) => (
                  <tr key={`ja3-${row.id}`}>
                    <td>{formatTimestamp(row.timestamp)}</td>
                    <td className="device-mac">{row.device_mac}</td>
                    <td className="domain ja3-hash">{row.ja3_hash}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* --- LINE 2: mDNS --- */}
      <div className="telemetry-row">
        {/* We reuse telemetry-col so it aligns perfectly. You can also add a custom class if you want it to stretch full-width */}
        <div className="telemetry-col">
          <h3 className="telemetry-subtitle">mDNS ({mdns.length})</h3>
          <div className="dns-table-container telemetry-scroll">
            <table className="dns-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Device</th>
                  <th>Service</th>
                </tr>
              </thead>
              <tbody>
                {mdns.map((row) => (
                  <tr key={`mdns-${row.id}`}>
                    <td>{formatTimestamp(row.timestamp)}</td>
                    <td className="device-mac">{row.device_mac}</td>
                    <td className="domain">{row.service_name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
    </section>
  );
};

export default TelemetryTables;