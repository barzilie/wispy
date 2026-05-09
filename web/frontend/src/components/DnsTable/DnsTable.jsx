import React, { useRef, useEffect } from 'react';
import './DnsTable.css';
import { formatTimestamp } from './DnsTable.logic';

const DnsTable = ({
  dnsQueries,
  dnsTotal = 0,
  onLoadMore,
  hasMoreDns = false,
  loadingMoreDns = false,
}) => {
  const scrollRootRef = useRef(null);
  const sentinelRef = useRef(null);

  useEffect(() => {
    const root = scrollRootRef.current;
    const target = sentinelRef.current;
    if (!root || !target || !hasMoreDns) return;

    const obs = new IntersectionObserver(
      (entries) => {
        const hit = entries.some((e) => e.isIntersecting);
        if (hit && hasMoreDns && !loadingMoreDns && onLoadMore) {
          onLoadMore();
        }
      },
      { root, rootMargin: '120px', threshold: 0 },
    );
    obs.observe(target);
    return () => obs.disconnect();
  }, [hasMoreDns, loadingMoreDns, onLoadMore]);

  return (
    <section className="section">
      <h2>
        🌐 DNS queries ({dnsQueries.length}
        {dnsTotal > dnsQueries.length ? ` of ${dnsTotal}` : ''})
      </h2>
      <div className="dns-table-container" ref={scrollRootRef}>
        <table className="dns-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Device</th>
              <th>Domain</th>
            </tr>
          </thead>
          <tbody>
            {dnsQueries.map((query) => (
              <tr key={query.id}>
                <td>{formatTimestamp(query.timestamp)}</td>
                <td className="device-mac">{query.device_mac}</td>
                <td className="domain">{query.domain}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div ref={sentinelRef} className="dns-scroll-sentinel" aria-hidden />
        {loadingMoreDns && (
          <div className="dns-loading-more">Loading older queries…</div>
        )}
        {!hasMoreDns && dnsQueries.length > 0 && (
          <div className="dns-end-hint">End of captured DNS log</div>
        )}
      </div>
    </section>
  );
};

export default DnsTable;
