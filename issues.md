# WiSpy — deferred issues

Tracked follow-ups from the TA extension code review (medium and low priority). Critical and high items were addressed in the same change set.

---

## Medium priority

### Flow session merge: SNI should win over DNS

**File:** `analysis/storage.py` — `upsert_flow_session()`

When aggregating within the 60s idle window, `host_source` and `dst_host` only update if the new value is not `"unknown"`. A row labeled via DNS is not upgraded when SNI arrives later in the same window.

**Fix:** Prefer `sni` > `dns` > `unknown` when merging `dst_host` and `host_source`.

---

### Flow tracking scope vs BPF

**File:** `core/sniffer.py` — `_track_packet_flow()`

Flow tracking runs on every `IP` packet in `process_packet`, including DHCP/DNS on the AP segment, not only client↔internet traffic on BPF ports.

**Fix:** Restrict flow keys to TCP/UDP with ports matching the capture intent, or only private→public tuples.

---

### Pattern heuristics tuning

**File:** `analysis/patterns.py`

- `SYSTEM_UPDATE` includes `g.doubleclick.net` while the sniffer filters ad DNS — inconsistent labeling.
- `MEDIA_STREAMING` can false-positive on `total_bytes > 5MB` across sampled flows.
- Document or tighten heuristics for lab demos.

---

### Plaintext body size cap

**Files:** `core/sniffer.py`, `analysis/storage.py`

Full HTTP/SMTP payloads are stored in `plaintext_events.body`. Consider truncating at insert (e.g. 4–8 KB) to limit DB growth and accidental over-capture.

---

### DNS correlation cache memory

**File:** `analysis/correlation.py`

`_dns_ip_cache` only evicts on TTL lookup. High-cardinality DNS can grow memory until process restart.

**Fix:** Max-size LRU or periodic sweep.

---

### Duplicated Flask pagination helpers

**File:** `web/app.py`

`api_flows` and `api_plaintext` duplicate `api_dns` cursor/pagination logic.

**Fix:** Extract a shared `_telemetry_feed()` helper.

---

### Real-mode AP deployment health checks

**File:** `web/app.py` — `select_network()`

Immediate-exit checks were added for hostapd/dnsmasq/sniffer. Daemons can still die shortly after start on bad config.

**Fix:** Optional delayed re-check or log tail in API error response.

---

## Low priority

### Style / polish

- Trailing blank lines in `analysis/storage.py`, `web/app.py`, `core/sniffer.py`.
- `Impl_report.md` missing trailing newline at EOF.
- `AgenticPanel` is a thin wrapper over `RecommendationsPanel` — document or merge names in `FILES_OVERVIEW.md`.

---

### Tests in minimal environments

**File:** `tests/test_extension.py`

Imports `analysis.storage` which loads `python-dotenv`. Document running tests inside `.venv` (same as `tests/test_storage.py`).

---

### `include_patterns` API flag

**File:** `web/app.py`

`GET /api/data?include_patterns=0` skips pattern work for lighter polls. Frontend still requests patterns by default; no UI toggle yet.

---

### Legacy template UI

**File:** `web/templates/index.html`

Does not show flows, plaintext, or agentic tabs (React dashboard does).

---

## Resolved (for reference)

| Issue | Resolution |
|-------|------------|
| Missing `datetime` in sniffer | `from datetime import datetime` in `core/sniffer.py` |
| DNS A/AAAA rdata parsing | `_dns_rr_to_ip()` with `socket.inet_ntoa` / `inet_ntop` |
| `/api/data` pattern cost | TTL cache + lower poll query limits in `analysis/patterns.py` |
| Patterns not in UI | `DeviceCard` shows `patterns` and `flow_stats` |
| Sniffer without root | `WISPY_SNIFFER_SUDO`, startup check, `sniffer_warning` in API response |
| Binary `data/wispy.db` in diff | Restore before commit; keep gitignored |
