import React from 'react';
import './DnsTable.css';
import { formatTimestamp } from './DnsTable.logic';

const DnsTable = ({ dnsQueries }) => {
  return (
    <section className="section">
      <h2>🌐 Recent DNS Queries ({dnsQueries.length})</h2>
      <div className="dns-table-container">
        <table className="dns-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Device</th>
              <th>Domain</th>
            </tr>
          </thead>
          <tbody>
            {dnsQueries.slice(0, 50).map((query) => (
              <tr key={query.id}>
                <td>{formatTimestamp(query.timestamp)}</td>
                <td className="device-mac">{query.device_mac}</td>
                <td className="domain">{query.domain}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default DnsTable;
