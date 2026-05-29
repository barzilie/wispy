import { useState, useEffect, useCallback, useRef } from 'react';

const PAGE_SIZE = 200;

/**
 * Live devices + DNS with incremental updates and cursor pagination for infinite scroll.
 */
const useWispyData = (refreshInterval = 2000) => {
  const [devices, setDevices] = useState([]);
  const [dnsQueries, setDnsQueries] = useState([]);
  const [dnsTotal, setDnsTotal] = useState(0);
  const [tlsSni, setTlsSni] = useState([]);
  const [ja3Rows, setJa3Rows] = useState([]);
  const [mdnsRows, setMdnsRows] = useState([]);
  const [flows, setFlows] = useState([]);
  const [flowsTotal, setFlowsTotal] = useState(0);
  const [plaintextEvents, setPlaintextEvents] = useState([]);
  const [plaintextTotal, setPlaintextTotal] = useState(0);
  const [error, setError] = useState(null);
  const [loadingMoreDns, setLoadingMoreDns] = useState(false);
  const [olderExhausted, setOlderExhausted] = useState(false);
  const maxIdRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const loadInitial = async () => {
      try {
        const [dnsRes, dataRes] = await Promise.all([
          fetch(`/api/dns?limit=${PAGE_SIZE}`),
          fetch('/api/data?include_dns=0'),
        ]);
        if (!dnsRes.ok || !dataRes.ok) {
          throw new Error('Failed to fetch monitoring data');
        }
        const dnsJson = await dnsRes.json();
        const dataJson = await dataRes.json();
        if (cancelled) return;
        const rows = dnsJson.dns || [];
        setDnsQueries(rows);
        setDnsTotal(dnsJson.total ?? 0);
        setDevices(dataJson.devices || []);
        setTlsSni(dataJson.tls_sni || []);
        setJa3Rows(dataJson.ja3 || []);
        setMdnsRows(dataJson.mdns || []);
        setFlows(dataJson.flows || []);
        setFlowsTotal(dataJson.flows_total ?? 0);
        setPlaintextEvents(dataJson.plaintext || []);
        setPlaintextTotal(dataJson.plaintext_total ?? 0);
        setOlderExhausted((dnsJson.total ?? 0) <= rows.length);
        if (rows.length) {
          maxIdRef.current = Math.max(...rows.map((r) => r.id));
        } else {
          maxIdRef.current = null;
        }
        setError(null);
      } catch (err) {
        if (!cancelled) {
          console.error('Error fetching data:', err);
          setError(err.message);
        }
      }
    };

    loadInitial();

    const interval = setInterval(async () => {
      try {
        const dataRes = await fetch('/api/data?include_dns=0');
        if (!dataRes.ok) throw new Error('Failed to fetch devices');
        const dataJson = await dataRes.json();
        if (cancelled) return;
        setDevices(dataJson.devices || []);
        setDnsTotal(dataJson.dns_total ?? 0);
        setTlsSni(dataJson.tls_sni || []);
        setJa3Rows(dataJson.ja3 || []);
        setMdnsRows(dataJson.mdns || []);
        setFlows(dataJson.flows || []);
        setFlowsTotal(dataJson.flows_total ?? 0);
        setPlaintextEvents(dataJson.plaintext || []);
        setPlaintextTotal(dataJson.plaintext_total ?? 0);

        const mid = maxIdRef.current;
        if (mid == null) {
          if ((dataJson.dns_total ?? 0) > 0) {
            const dnsRes = await fetch(`/api/dns?limit=${PAGE_SIZE}`);
            if (!dnsRes.ok || cancelled) return;
            const dj = await dnsRes.json();
            const rows = dj.dns || [];
            if (cancelled || !rows.length) return;
            setDnsQueries(rows);
            setDnsTotal(dj.total ?? 0);
            maxIdRef.current = Math.max(...rows.map((r) => r.id));
            setOlderExhausted((dj.total ?? 0) <= rows.length);
          }
          return;
        }

        const incRes = await fetch(`/api/dns?after_id=${mid}&limit=500`);
        if (!incRes.ok) return;
        const incJson = await incRes.json();
        const fresh = incJson.dns || [];
        if (cancelled || !fresh.length) return;

        setDnsQueries((prev) => {
          const byId = new Map(prev.map((r) => [r.id, r]));
          fresh.forEach((r) => byId.set(r.id, r));
          const next = Array.from(byId.values()).sort((a, b) => b.id - a.id);
          maxIdRef.current = next.length ? next[0].id : mid;
          return next;
        });
        setError(null);
      } catch (err) {
        if (!cancelled) {
          console.error('Error polling:', err);
          setError(err.message);
        }
      }
    }, refreshInterval);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [refreshInterval]);

  useEffect(() => {
    if (dnsTotal > 0 && dnsQueries.length >= dnsTotal) {
      setOlderExhausted(true);
    }
  }, [dnsQueries.length, dnsTotal]);

  const loadMoreDns = useCallback(async () => {
    if (loadingMoreDns || olderExhausted) return;
    const oldest = dnsQueries.length ? dnsQueries[dnsQueries.length - 1].id : null;
    if (oldest == null) return;

    setLoadingMoreDns(true);
    try {
      const res = await fetch(`/api/dns?before_id=${oldest}&limit=${PAGE_SIZE}`);
      if (!res.ok) throw new Error('Failed to load older DNS rows');
      const j = await res.json();
      const older = j.dns || [];
      if (older.length === 0) {
        setOlderExhausted(true);
        return;
      }
      const existingIds = new Set(dnsQueries.map((r) => r.id));
      const appended = older.filter((r) => !existingIds.has(r.id));
      if (appended.length === 0) {
        setOlderExhausted(true);
        return;
      }
      setDnsQueries((prev) => [...prev, ...appended]);
      if (older.length < PAGE_SIZE) {
        setOlderExhausted(true);
      }
      setError(null);
    } catch (err) {
      console.error('loadMoreDns:', err);
      setError(err.message);
    } finally {
      setLoadingMoreDns(false);
    }
  }, [dnsQueries, loadingMoreDns, olderExhausted]);

  const hasMoreDns = !olderExhausted && dnsQueries.length < dnsTotal;

  return {
    devices,
    dnsQueries,
    dnsTotal,
    tlsSni,
    ja3Rows,
    mdnsRows,
    flows,
    flowsTotal,
    plaintextEvents,
    plaintextTotal,
    error,
    loadMoreDns,
    loadingMoreDns,
    hasMoreDns,
  };
};

export default useWispyData;
