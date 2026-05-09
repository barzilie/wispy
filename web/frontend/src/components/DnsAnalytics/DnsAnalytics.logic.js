/** Bucket ISO timestamps to minute key for volume-over-time. */
export const bucketMinute = (timestamp) => {
  if (!timestamp) return null;
  const d = new Date(timestamp);
  if (Number.isNaN(d.getTime())) return null;
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

export const buildQueriesPerMinute = (dnsRows) => {
  const counts = new Map();
  for (const row of dnsRows) {
    const key = bucketMinute(row.timestamp);
    if (!key) continue;
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  return [...counts.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([minute, count]) => ({ minute, queries: count }));
};

export const buildTopDomains = (dnsRows, limit = 12) => {
  const counts = new Map();
  for (const row of dnsRows) {
    const d = (row.domain || '').toLowerCase();
    if (!d) continue;
    counts.set(d, (counts.get(d) || 0) + 1);
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([domain, count]) => ({ domain, count }));
};
