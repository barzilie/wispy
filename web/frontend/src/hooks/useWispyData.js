import { useState, useEffect, useCallback, useRef } from 'react';

const PAGE_SIZE = 200;
const DATA_URL = '/api/data?include_dns=0';
const POLL_DATA_URL = '/api/data?include_dns=0&include_patterns=0';

const applyTelemetry = (dataJson, setters) => {
  setters.setDevices(dataJson.devices || []);
  setters.setTlsSni(dataJson.tls_sni || []);
  setters.setJa3Rows(dataJson.ja3 || []);
  setters.setMdnsRows(dataJson.mdns || []);
  setters.setFlows(dataJson.flows || []);
  setters.setFlowsTotal(dataJson.flows_total ?? 0);
  setters.setPlaintextEvents(dataJson.plaintext || []);
  setters.setPlaintextTotal(dataJson.plaintext_total ?? 0);
};

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

  const telemetrySetters = {
    setDevices,
    setTlsSni,
    setJa3Rows,
    setMdnsRows,
    setFlows,
    setFlowsTotal,
    setPlaintextEvents,
    setPlaintextTotal,
  };

  // Effect 1: Handles Initial Load & Background Polling Loop
  useEffect(() => {
    let cancelled = false;
    let timeoutId;

    const syncDnsRows = (rows, total) => {
      setDnsQueries(rows);
      setDnsTotal(total);
      setOlderExhausted(total <= rows.length);
      if (rows.length) {
        maxIdRef.current = Math.max(...rows.map((r) => r.id));
      } else {
        maxIdRef.current = null;
      }
    };

    const refreshDns = async () => {
      const mid = maxIdRef.current;
      if (mid == null) {
        const dnsRes = await fetch(`/api/dns?limit=${PAGE_SIZE}`);
        if (!dnsRes.ok || cancelled) return false;
        const dj = await dnsRes.json();
        const rows = dj.dns || [];
        if (cancelled || !rows.length) return false;
        syncDnsRows(rows, dj.total ?? 0);
        return true;
      }

      const incRes = await fetch(`/api/dns?after_id=${mid}&limit=500`);
      if (!incRes.ok || cancelled) return false;
      const incJson = await incRes.json();
      const fresh = incJson.dns || [];
      if (!fresh.length) return false;

      setDnsQueries((prev) => {
        const byId = new Map(prev.map((r) => [r.id, r]));
        fresh.forEach((r) => byId.set(r.id, r));
        const next = Array.from(byId.values()).sort((a, b) => b.id - a.id).slice(0, 1000);
        maxIdRef.current = next.length ? next[0].id : mid;
        return next;
      });
      if (incJson.total != null) {
        setDnsTotal(incJson.total);
      }
      return true;
    };

    const loadInitial = async () => {
      let dnsOk = false;
      let dataOk = false;

      try {
        const dnsRes = await fetch(`/api/dns?limit=${PAGE_SIZE}`);
        if (dnsRes.ok) {
          const dnsJson = await dnsRes.json();
          if (!cancelled) {
            syncDnsRows(dnsJson.dns || [], dnsJson.total ?? 0);
            dnsOk = true;
          }
        }
      } catch (err) {
        console.error('Error fetching DNS:', err);
      }

      try {
        const dataRes = await fetch(DATA_URL);
        if (dataRes.ok) {
          const dataJson = await dataRes.json();
          if (!cancelled) {
            applyTelemetry(dataJson, telemetrySetters);
            if (dataJson.dns_total != null) {
              setDnsTotal(dataJson.dns_total);
            }
            dataOk = true;
          }
        }
      } catch (err) {
        console.error('Error fetching telemetry:', err);
      }

      if (!cancelled) {
        if (dnsOk || dataOk) {
          setError(null);
        } else {
          setError('Failed to fetch monitoring data');
        }
      }
    };

    const pollMonitoringData = async () => {
      if (cancelled) return;

      let telemetryOk = false;

      try {
        const dataRes = await fetch(POLL_DATA_URL);
        if (dataRes.ok) {
          const dataJson = await dataRes.json();
          if (!cancelled) {
            applyTelemetry(dataJson, telemetrySetters);
            setDnsTotal(dataJson.dns_total ?? 0);
            telemetryOk = true;
          }
        }
      } catch (err) {
        console.error('Error polling telemetry:', err);
      }

      try {
        const dnsOk = await refreshDns();
        if (!cancelled && (telemetryOk || dnsOk)) {
          setError(null);
        } else if (!cancelled && !telemetryOk) {
          setError('Failed to refresh monitoring data');
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Error polling DNS:', err);
          setError(err.message);
        }
      }

      // Schedule the next poll ONLY after this one completes
      if (!cancelled) {
        timeoutId = setTimeout(pollMonitoringData, refreshInterval);
      }
    };

    // Kick off initial setup and start loop
    loadInitial();
    pollMonitoringData();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [refreshInterval]);

  // Effect 2: Check for exhaustion state
  useEffect(() => {
    if (dnsTotal > 0 && dnsQueries.length >= dnsTotal) {
      setOlderExhausted(true);
    }
  }, [dnsQueries.length, dnsTotal]);

  // Infinite Scroll Pagination Trigger
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