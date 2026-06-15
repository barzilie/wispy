# WiSpy Files Overview

Quick reference for where everything is and what it does.

## 🎛️ Configuration & Control

| File | Purpose | Edit This To... |
|------|---------|-----------------|
| `.env` | Environment config | Set API keys, WiFi interface, Flask host/port |
| `config.py` | Central configuration | Reads `.env` and exposes shared settings |

## 🌐 Backend (Python/Flask)

| File | Purpose |
|------|---------|
| `web/app.py` | Flask API server (all endpoints) |
| `core/scanner.py` | WiFi scanning |
| `core/sniffer.py` | Packet capture: DNS, DHCP, mDNS, TLS (SNI/JA3), flow sessions, plaintext HTTP/SMTP |
| `core/ap_manager.py` | Rogue AP setup (hostapd/dnsmasq) |
| `core/fingerprint.py` | Device OS detection |
| `analysis/storage.py` | SQLite: devices, DNS, TLS, mDNS, `flow_sessions`, `plaintext_events` |
| `analysis/correlation.py` | In-memory DNS reply → IP cache for flow hostname labeling |
| `analysis/patterns.py` | Per-device usage-pattern heuristics for agentic context |
| `analysis/dns_filters.py` | Regex helpers to skip ad-tech DNS before storage |
| `analysis/agentic/` | Unified Gemini module: `client`, `context`, investigation + recommend prompts |
| `analysis/recommender.py` | Thin shim → `analysis.agentic` |
| `extension.md` | TA feedback extension plan and track roadmap |

## ⚛️ Frontend (React)

| Directory | Purpose |
|-----------|---------|
| `web/frontend/src/components/` | All React components |
| `web/frontend/src/hooks/` | Custom React hooks |
| `web/frontend/src/App.js` | Main app with screen flow |

### Component Structure (Each has 3 files)

```
ComponentName/
├── ComponentName.jsx       # UI/HTML
├── ComponentName.logic.js  # Business logic
└── ComponentName.css       # Styling
```

**Available Components:**
- `StartScreen` - Initial "Start Hacking" screen
- `NetworkSelectionScreen` - WiFi network picker
- `MonitoringScreen` - Main dashboard wrapper
- `Header` - App header
- `DeviceList` - Grid of device cards
- `DeviceCard` - Single device display
- `DnsTable` - DNS queries (infinite scroll via `/api/dns`)
- `DnsAnalytics` - DNS charts (Recharts)
- `TelemetryTables` - TLS SNI, JA3, and mDNS tables
- `FlowAnalytics` - Session reconnaissance (flows, DNS/SNI resolution badges)
- `PlaintextPanel` - Cleartext HTTP/SMTP leaks with expandable bodies
- `AgenticPanel` / `RecommendationsPanel` - Tabbed AI: session investigation + attack suggestions

## 📚 Documentation

| File | Purpose |
|------|---------|
| `README.md` | Project overview & scope |
| `CLAUDE.md` | Guide for Claude Code (architecture, commands) |
| `INSTALLATION.md` | Kali Linux setup instructions |
| `plan.md` | Development plan & decisions |
| `Impl_report.md` | Implementation details & debugging |
| `web/frontend/COMPONENTS.md` | React component documentation |
| `FILES_OVERVIEW.md` | This file |

## 🗄️ Data & Storage

| File/Directory | Purpose |
|----------------|---------|
| `data/wispy.db` | SQLite DB: devices, DNS, TLS, mDNS, `flow_sessions`, `plaintext_events` |
| `data/` | Runtime data (gitignored) |

## 🧪 Testing

| File | Purpose |
|------|---------|
| `tests/test_storage.py` | SQLite storage tests |
| `tests/test_dns_filters.py` | Ad-domain DNS filter tests |
| `tests/test_extension.py` | Flow sessions, plaintext, correlation, patterns |

## 🚀 Entry Points

| File | Purpose | How to Run |
|------|---------|-----------|
| `start_wispy.py` | Start Flask + React together | `python start_wispy.py` |
| `web/app.py` | Flask API server | `python web/app.py` |
| `web/frontend/` | React dev server | `cd web/frontend && npm start` |
| `main.py` | Full system launcher (legacy CLI) | `sudo python main.py` |

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `web/frontend/package.json` | React dependencies |
| `.gitignore` | Git exclusions |
| `.env` | Environment variables |

---

## 📍 Quick Navigation

**Want to change...**

→ **React components?** Go to `web/frontend/src/components/`

→ **API endpoints?** Edit `web/app.py`

→ **Database schema?** Edit `analysis/storage.py`

→ **Styling?** Edit component `.css` files

→ **App flow logic?** Edit `web/frontend/src/hooks/useAppFlow.js`

---

## 🎯 Common Tasks

### Create new React component
```bash
mkdir web/frontend/src/components/MyComponent
touch web/frontend/src/components/MyComponent/MyComponent.{jsx,logic.js,css}
```

### Check current status
```bash
curl http://localhost:5000/api/status
```

### Start the full stack
```bash
python start_wispy.py
```
