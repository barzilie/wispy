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

## 🎯 Editing Mock Devices & DNS Data

**File:** `mock_data.py`

Run this script to populate the database with fake devices:

```bash
# Generate fresh mock data
python mock_data.py

# Add more queries to existing data
python mock_data.py --more

# Reset and regenerate
python mock_data.py --reset
```

**Customize devices in `mock_data.py`:**
```python
MOCK_DEVICES = [
    {
        "mac": "a4:83:e7:12:34:56",
        "hostname": "Johns-iPhone",
        "vendor": "Apple",
        "os_guess": "iOS",
        "domains": [
            "instagram.com",
            "twitter.com",
            # Add more domains here
        ]
    },
    # Add more devices here...
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
✅ Device data comes from `mock_data.py` script
✅ No actual wireless adapter needed
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
| **Mock Devices/DNS** | `mock_data.py` | Run script to regenerate DB data |
| **Mode Control** | `.env` or auto-detect | Set once, applies on startup |
| **Check Mode** | Terminal output or `/api/status` | Anytime while running |

**Default Behavior:**
- macOS → Mock mode ✅ (safe for dev)
- Kali Linux → Real mode ✅ (hardware required)
