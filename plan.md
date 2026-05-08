# WiSpy – Project Plan

## What is WiSpy
BGU Network Security course mini-project (due June 20, 2026).
A rogue Wi-Fi Access Point tool that passively monitors connected devices, captures DNS traffic, fingerprints devices, and uses Claude AI to recommend attack vectors based on collected data.

---

## Agreed Design Decisions

### Architecture
- Runs on **Kali Linux** with a **TP-Link TL-WN722N** adapter
- Two separate processes, each started independently:
  - Terminal 1: `python core/sniffer.py`
  - Terminal 2: `python web/app.py`
- Both read/write the same SQLite file — no shared memory, no threads
- Dashboard polls `/api/data` every 2 seconds

### Stack
- Python: Scapy, Flask, google-generativeai SDK
- JavaScript: vanilla (no framework)
- Storage: SQLite via raw `sqlite3` (Python stdlib, no extra dependency)
- AI: Google AI Studio (Gemini) for recommendations

### Monitoring Strategy
- **Focus on DNS only** — DNS is plain text even over HTTPS, reveals apps/services/behavior
- HTTP tracking dropped — too little unencrypted traffic in practice
- Device fingerprinting via: MAC OUI (vendor), TTL (OS guess), DHCP hostname

### Recommender
- Triggered **on demand** (user clicks button in dashboard)
- Reads devices + DNS from SQLite
- Builds a structured prompt and calls Claude API
- Returns plain text attack suggestions

---

## Data Schema (SQLite)

```sql
CREATE TABLE devices (
    mac         TEXT PRIMARY KEY,
    ip          TEXT,
    hostname    TEXT,
    vendor      TEXT,
    os_guess    TEXT,
    first_seen  TEXT,
    last_seen   TEXT
);

CREATE TABLE dns_requests (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_mac  TEXT,
    domain      TEXT,
    timestamp   TEXT
);
```

---

## Project File Structure

```
wispy/
├── core/
│   ├── scanner.py        # Wi-Fi environment scan (iwlist/iw)
│   ├── ap_manager.py     # Rogue AP via hostapd + dnsmasq
│   ├── deauth.py         # Scapy 802.11 deauth frames
│   ├── sniffer.py        # DNS packet capture → SQLite
│   └── fingerprint.py   # MAC OUI + TTL-based OS guess
│
├── analysis/
│   ├── storage.py        # SQLite read/write helpers
│   └── recommender.py   # Builds prompt → Claude API → returns suggestions
│
├── web/
│   ├── app.py            # Flask: GET /api/data, POST /api/recommend
│   ├── static/js/app.js  # Dashboard JS, polls every 2s
│   └── templates/
│       └── index.html    # Single-page dashboard
│
├── config/
│   ├── hostapd.conf      # AP config template
│   └── dnsmasq.conf      # DHCP/DNS config template
│
├── data/                 # Runtime SQLite db + logs (gitignored)
├── main.py               # CLI entry: starts threads, wires everything
├── requirements.txt
├── plan.md               # This file
└── README.md
```

---

## Development Plan (Ordered)

| Step | File(s) | What |
|------|---------|------|
| 1 | folders + `requirements.txt` + stubs | Project skeleton | ✅ Done |
| 2 | `analysis/storage.py` | SQLite schema + read/write helpers |
| 3 | `core/sniffer.py` | Scapy DNS capture → writes to SQLite |
| 4 | `core/fingerprint.py` | MAC OUI lookup + TTL OS guess |
| 5 | `core/scanner.py` | List nearby Wi-Fi networks |
| 6 | `core/ap_manager.py` | Start/stop rogue AP (hostapd + dnsmasq) |
| 7 | `core/deauth.py` | Deauth frame burst |
| 8 | `web/app.py` | Flask API (`/api/data`, `/api/recommend`) |
| 9 | `analysis/recommender.py` | Claude API integration |
| 10 | `web/` templates + JS | Dashboard UI (discuss design separately) |
| 11 | `main.py` | Optional launcher: starts sniffer + Flask as subprocesses |
| 12 | — | End-to-end test on Kali, demo prep |

### Critical path
Steps 1 → 2 → 3 → 8 → 9 can be built and demoed before the AP is set up.
Steps 5 → 6 → 7 (AP path) can be developed in parallel.

---

## Implementation Status
- Step 1 (environment + skeleton): ✅ Done
  - Kali Linux VM, USB passthrough, rtl8188eus driver via dkms
  - Monitor mode scripts (airmon-ng + iw)
  - Sudoers: Flask runs non-root, network commands whitelisted NOPASSWD
  - Python venv: scapy, Flask, anthropic, python-dotenv installed
  - subprocess established for shell orchestration
- Step 2 (storage.py): ✅ Done
  - SQLite via raw sqlite3, DB always at <project_root>/data/wispy.db
  - Tables: devices (mac PK, ip, hostname, vendor, os_guess, first_seen, last_seen)
  - Tables: dns_requests (id AUTOINCREMENT, device_mac, domain, timestamp)
  - Functions: init_db, upsert_device, insert_dns, get_devices, get_dns_requests, get_session_summary, reset_db
  - upsert_device uses COALESCE — partial updates never wipe existing fields
  - reset_db asks user to type 'yes' before deleting all data
  - All tests passing (tests/test_storage.py)
- Step 3 onwards: not started

## Still To Discuss
- Dashboard UI design (deferred — Step 10)

---

## Session Notes
- Keep everything as simple as possible — no over-engineering
- No websockets, no message queues, no complex abstractions
- DNS is the only traffic we monitor (HTTP dropped)
- Recommender uses Claude AI, not a static rule map
