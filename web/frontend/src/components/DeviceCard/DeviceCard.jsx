import React, { useMemo } from 'react';
import './DeviceCard.css';
import { formatTimestamp } from './DeviceCard.logic';

const takeUnique = (rows, mac, key, max) => {
  const forDev = rows.filter((r) => r.device_mac === mac);
  const seen = new Set();
  const out = [];
  for (const r of forDev) {
    const v = (r[key] || '').trim();
    if (!v || seen.has(v)) continue;
    seen.add(v);
    out.push(v);
    if (out.length >= max) break;
  }
  return out;
};

const DeviceCard = ({ device, dnsQueries = [], tlsSni = [], ja3Rows = [], mdnsRows = [] }) => {
  const previewDomains = useMemo(() => {
    const forDevice = dnsQueries.filter((q) => q.device_mac === device.mac);
    const seen = new Set();
    const ordered = [];
    for (const q of forDevice) {
      const d = (q.domain || '').trim();
      if (!d || seen.has(d)) continue;
      seen.add(d);
      ordered.push(d);
      if (ordered.length >= 8) break;
    }
    return ordered;
  }, [dnsQueries, device.mac]);

  const previewSni = useMemo(
    () => takeUnique(tlsSni, device.mac, 'sni', 4),
    [tlsSni, device.mac],
  );
  const previewJa3 = useMemo(
    () => takeUnique(ja3Rows, device.mac, 'ja3_hash', 3),
    [ja3Rows, device.mac],
  );
  const previewMdns = useMemo(
    () => takeUnique(mdnsRows, device.mac, 'service_name', 4),
    [mdnsRows, device.mac],
  );

  const dhcpLine = device.dhcp_params
    ? String(device.dhcp_params).trim()
    : '';

  const patterns = device.patterns || [];
  const flowStats = device.flow_stats;

  return (
    <div className="device-card">
      <div className="device-header">
        <span className="device-name">{device.hostname || 'Unknown Device'}</span>
        <span className="device-os">{device.os_guess}</span>
      </div>
      <div className="device-info">
        <p><strong>MAC</strong> {device.mac}</p>
        <p><strong>IP</strong> {device.ip}</p>
        <p><strong>Vendor</strong> {device.vendor}</p>
        <p><strong>First Seen</strong> {formatTimestamp(device.first_seen)}</p>
        <p><strong>Last Seen</strong> {formatTimestamp(device.last_seen)}</p>
        {dhcpLine ? (
          <p className="device-dhcp55" title="DHCP Option 55 (param request list)">
            <strong>DHCP opt 55</strong> <span className="device-dhcp55-value">{dhcpLine}</span>
          </p>
        ) : null}
        {flowStats ? (
          <p className="device-flow-stats">
            <strong>Flows</strong>{' '}
            {flowStats.total_flows} sessions · {flowStats.total_packets} pkts
          </p>
        ) : null}
      </div>
      {patterns.length > 0 && (
        <div className="device-patterns">
          <span className="device-dns-preview-label">Usage patterns</span>
          <ul className="device-pattern-list">
            {patterns.map((p) => (
              <li
                key={p.tag}
                className={`device-pattern-badge severity-${p.severity || 'info'}`}
                title={p.desc}
              >
                {p.name}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="device-dns-preview">
        <span className="device-dns-preview-label">Recent DNS</span>
        {previewDomains.length ? (
          <ul className="device-dns-preview-list">
            {previewDomains.map((d) => (
              <li key={d} title={d}>{d}</li>
            ))}
          </ul>
        ) : (
          <p className="device-dns-preview-empty">No queries for this MAC in the loaded log.</p>
        )}
      </div>
      {(previewSni.length > 0 || previewJa3.length > 0 || previewMdns.length > 0) && (
        <div className="device-meta-telemetry">
          {previewSni.length > 0 && (
            <div className="device-meta-block">
              <span className="device-dns-preview-label">TLS SNI</span>
              <ul className="device-dns-preview-list">
                {previewSni.map((s) => (
                  <li key={s} title={s}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {previewJa3.length > 0 && (
            <div className="device-meta-block">
              <span className="device-dns-preview-label">JA3</span>
              <ul className="device-dns-preview-list device-ja3-list">
                {previewJa3.map((h) => (
                  <li key={h} title={h}>{h}</li>
                ))}
              </ul>
            </div>
          )}
          {previewMdns.length > 0 && (
            <div className="device-meta-block">
              <span className="device-dns-preview-label">mDNS</span>
              <ul className="device-dns-preview-list">
                {previewMdns.map((m) => (
                  <li key={m} title={m}>{m}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DeviceCard;
