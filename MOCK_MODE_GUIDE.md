# Mock Mode Control Guide

## 📋 Quick Reference

### Where to Control Mock Data

1. **Mock Networks**: `mock/mock_networks.py`
2. **Mock Devices**: `mock_data.py` (run manually)
3. **Mode Configuration**: `.env` file or auto-detect

---

## 🎯 Editing Mock WiFi Networks

**File:** `mock/mock_networks.py`

```python
MOCK_NETWORKS = [
    {
        "ssid": "HomeNetwork_5G",      # Change network name
        "bssid": "00:11:22:33:44:55",  # Change MAC address
        "channel": 6,                   # Change WiFi channel (1-13)
        "encryption": "WPA",            # "Open" or "WPA"
        "signal": -45                   # Change signal (-30 to -90)
    },
    # Add your own networks here...
]
```

**To add more networks:** Just copy the block and change the values!

---

## 🎯 Editing Mock Devices & Telemetry Data

**File:** `mock_data.py`

Run this script to populate `data/wispy.db` with fake **devices**, **DNS**, **TLS SNI**, **JA3**, **mDNS**, and **DHCP Option 55** (`dhcp_params` on each device), matching what the sniffer persists in real mode.

```bash
# Generate / refresh mock data (upserts devices; adds DNS + telemetry rows)
python mock_data.py

# Extra DNS rows only (uses insert_dns; does not clear tables)
python mock_data.py --more

# Clear ALL telemetry + devices, then regenerate a full mock dataset
python mock_data.py --reset

# More DNS rows per device when regenerating after --reset
python mock_data.py --reset --many
```

**Customize devices in `mock_data.py`:** each entry in `MOCK_DEVICES` can include:

- `mac`, `ip`, `hostname`, `vendor`, `os_guess`
- `dhcp_params` — comma-separated Option 55–style parameter list string
- `domains` — pool for synthetic `dns_requests`
- `sni_hosts` — pool for synthetic `tls_sni` rows
- `ja3_samples` — pool for synthetic `ja3_fingerprints` (32-hex style hashes)
- `mdns_services` — pool for synthetic `mdns_broadcasts` (e.g. `_airplay._tcp.local`)

Example shape:

```python
MOCK_DEVICES = [
    {
        "mac": "a4:83:e7:12:34:56",
        "ip": "192.168.50.10",
        "hostname": "Johns-iPhone",
        "vendor": "Apple",
        "os_guess": "iOS",
        "dhcp_params": "1,3,6,15,28,119,121",
        "domains": ["api.instagram.com", "www.youtube.com"],
        "sni_hosts": ["api.instagram.com", "www.youtube.com"],
        "ja3_samples": ["e7d705a3286e1ea8e910c2f49a1a4d4f"],
        "mdns_services": ["_sleep-proxy._udp.local"],
    },
]
```

---

## 🔄 Mock Mode vs Real Mode

### Automatic Detection (Default)
```bash
# On macOS → Mock mode automatically enabled
python web/app.py

# On Kali Linux → Real mode automatically enabled
sudo python web/app.py
```

### Manual Override

**Force Mock Mode (in `.env`):**
```bash
WISPY_MOCK_MODE=true
```

**Force Real Mode (in `.env`):**
```bash
WISPY_MOCK_MODE=false
```

**One-time override (command line):**
```bash
# Force mock mode
WISPY_MOCK_MODE=true python web/app.py

# Force real mode (requires Kali + hardware)
WISPY_MOCK_MODE=false sudo python web/app.py
```

---

## 🖥️ What Changes Between Modes?

### Mock Mode (macOS Development)
✅ WiFi scan returns fake networks from `mock/mock_networks.py`
✅ Telemetry in the dashboard comes from SQLite — populate with `mock_data.py` (devices, DNS, TLS SNI, JA3, mDNS, DHCP Option 55)
✅ No actual wireless adapter needed for UI/API work
✅ Safe for development

### Real Mode (Kali Production)
✅ WiFi scan uses actual `core/scanner.py` with hardware
✅ Device data comes from real packet capture
✅ Requires TP-Link TL-WN722N adapter
✅ Must run as root with `sudo`

---

## 📊 Check Current Mode

### In Terminal:
```bash
python web/app.py
```

Output will show:
```
============================================================
🕵️  WiSpy Network Surveillance System
============================================================
Platform:        Darwin
Mock Mode:       ENABLED          ← Current mode
WiFi Interface:  Mock Data        ← Shows "wlan0" in real mode
Flask Server:    0.0.0.0:5000
============================================================
```

### Via API:
```bash
curl http://localhost:5000/api/status
```

Response:
```json
{
  "mock_mode": true,
  "mode_info": {
    "platform": "Darwin",
    "is_macos": true,
    "is_kali": false,
    "mock_mode": true
  }
}
```

---

## 🚀 Quick Start Scenarios

### Scenario 1: Development on macOS
```bash
# 1. Edit mock networks
nano mock/mock_networks.py

# 2. Generate mock device data
python mock_data.py

# 3. Start Flask (auto-detects macOS → mock mode)
python web/app.py

# 4. Start React
cd web/frontend && npm start

# 5. Open http://localhost:3001
```

### Scenario 2: Testing on Kali
```bash
# 1. Disable mock mode (optional, auto-detects Kali)
# Edit .env: WISPY_MOCK_MODE=false

# 2. Start Flask as root (needs hardware access)
sudo .venv/bin/python web/app.py

# 3. System will use real wireless scanner
```

### Scenario 3: Force Mock Mode on Kali (for testing)
```bash
# Set mock mode in .env
echo "WISPY_MOCK_MODE=true" >> .env

# Run normally (no sudo needed)
python web/app.py
```

---

## 📝 Summary

| What | Where | When |
|------|-------|------|
| **Mock WiFi Networks** | `mock/mock_networks.py` | Edit anytime, affects next scan |
| **Mock DB (devices + DNS + TLS/JA3/mDNS + DHCP 55)** | `mock_data.py` | Run script (`--reset` for full wipe + regenerate) |
| **Mode Control** | `.env` or auto-detect | Set once, applies on startup |
| **Check Mode** | Terminal output or `/api/status` | Anytime while running |

**Default Behavior:**
- macOS → Mock mode ✅ (safe for dev)
- Kali Linux → Real mode ✅ (hardware required)
