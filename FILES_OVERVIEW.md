# WiSpy Files Overview

Quick reference for where everything is and what it does.

## 🎛️ Configuration & Control

| File | Purpose | Edit This To... |
|------|---------|-----------------|
| `.env` | Environment config | Override mock mode, set API keys |
| `config.py` | Central configuration | Auto-detects platform, reads `.env` |
| `MOCK_MODE_GUIDE.md` | Mock system docs | Learn how to use mock data (networks, `mock_data.py`, modes) |

## 🧪 Mock Data (Development)

| File | Purpose | Edit This To... |
|------|---------|-----------------|
| `mock/mock_networks.py` | WiFi networks for scanning | Add/edit fake networks |
| `mock_data.py` | SQLite populator: devices, DNS, TLS SNI, JA3, mDNS, DHCP Option 55 | Edit `MOCK_DEVICES` or run with `--reset` / `--more` |
| `mock/README.md` | Mock system documentation | - |

**Usage:**
```bash
# Edit networks
nano mock/mock_networks.py

# Generate device data
python mock_data.py
```

## 🌐 Backend (Python/Flask)

| File | Purpose |
|------|---------|
| `web/app.py` | Flask API server (all endpoints) |
| `core/scanner.py` | WiFi scanning (real mode) |
| `core/sniffer.py` | Packet capture: DNS, DHCP (incl. Option 55), mDNS, TLS ClientHello (SNI + JA3) |
| `core/ap_manager.py` | Rogue AP setup (hostapd/dnsmasq) |
| `core/fingerprint.py` | Device OS detection |
| `analysis/storage.py` | SQLite layer (devices, DNS, `tls_sni`, `ja3_fingerprints`, `mdns_broadcasts`) |
| `analysis/dns_filters.py` | Regex helpers to skip ad-tech DNS before storage |
| `analysis/recommender.py` | Gemini-based session summary → recommendations |

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
- `RecommendationsPanel` - AI recommendations

## 📚 Documentation

| File | Purpose |
|------|---------|
| `README.md` | Project overview & scope |
| `CLAUDE.md` | Guide for Claude Code (architecture, commands) |
| `INSTALLATION.md` | Kali Linux setup instructions |
| `plan.md` | Development plan & decisions |
| `Impl_report.md` | Implementation details & debugging |
| `MOCK_MODE_GUIDE.md` | **How to control mock data** |
| `web/frontend/COMPONENTS.md` | React component documentation |
| `FILES_OVERVIEW.md` | This file |

## 🗄️ Data & Storage

| File/Directory | Purpose |
|----------------|---------|
| `data/wispy.db` | SQLite DB: devices (incl. `dhcp_params`), DNS, TLS SNI, JA3, mDNS |
| `data/` | Runtime data (gitignored) |

## 🧪 Testing

| File | Purpose |
|------|---------|
| `tests/test_storage.py` | SQLite storage tests |
| `tests/test_dns_filters.py` | Ad-domain DNS filter tests |

## 🚀 Entry Points

| File | Purpose | How to Run |
|------|---------|-----------|
| `web/app.py` | Flask API server | `python web/app.py` |
| `web/frontend/` | React dev server | `cd web/frontend && npm start` |
| `main.py` | Full system launcher (Kali only) | `sudo python main.py` |
| `mock_data.py` | Mock data generator | `python mock_data.py` |

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

→ **Mock WiFi networks?** Edit `mock/mock_networks.py`

→ **Mock devices?** Run `python mock_data.py` (or edit that file)

→ **React components?** Go to `web/frontend/src/components/`

→ **API endpoints?** Edit `web/app.py`

→ **Database schema?** Edit `analysis/storage.py`

→ **Styling?** Edit component `.css` files

→ **App flow logic?** Edit `web/frontend/src/hooks/useAppFlow.js`

---

## 🎯 Common Tasks

### Add a new mock network
```bash
# Edit this file
nano mock/mock_networks.py

# Restart Flask
python web/app.py
```

### Add mock device data
```bash
python mock_data.py --more
```

### Create new React component
```bash
mkdir web/frontend/src/components/MyComponent
touch web/frontend/src/components/MyComponent/MyComponent.{jsx,logic.js,css}
```

### Check current mode
```bash
curl http://localhost:5000/api/status
```

### Switch from mock to real mode
```bash
# In .env file
WISPY_MOCK_MODE=false
```
