# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WiSpy is a network security research tool designed for the BGU Network Security course. It creates a rogue Wi-Fi access point that monitors connected devices, captures DNS traffic, performs device fingerprinting, and uses AI to recommend attack vectors based on collected data.

**Critical Context:** This is an academic security research project. All operations are designed for controlled, authorized testing environments only.

## System Architecture

### Two-Process Design
The system runs as **two independent processes** that must be started separately:

1. **Main Process** (`main.py`): Scanner + Rogue AP + Sniffer (requires root)
2. **Dashboard Process** (`web/app.py`): Flask web interface (runs as non-root user)

Both processes communicate via a shared SQLite database at `data/wispy.db`. No websockets, no message queues, no shared memory.

### Core Components

- **`core/scanner.py`**: 802.11 beacon frame capture using Scapy. Switches interface to monitor mode via `airmon-ng`, performs channel-hopping across 2.4 GHz channels (1-13), collects SSID/BSSID/channel/encryption info.
- **`core/ap_manager.py`**: Rogue AP orchestration. Configures `hostapd` (fake AP daemon) and `dnsmasq` (DHCP/DNS server), enables IP forwarding and NAT via iptables.
- **`core/sniffer.py`**: DNS and DHCP packet capture. Runs continuously, writes to SQLite. Filters on UDP ports 53/67/68.
- **`core/fingerprint.py`**: Device identification via MAC OUI lookup (vendor) and TTL-based OS guessing.
- **`analysis/storage.py`**: SQLite wrapper with schema init, upsert logic using `COALESCE` for partial updates, and session summarization.
- **`web/app.py`**: Flask API serving `/api/data` (devices + DNS) and `/api/recommend` (AI suggestions).

### Data Flow
1. User runs `main.py` → scans networks → selects target → starts rogue AP
2. Victim connects to fake AP → DHCP assigns IP → sniffer captures DNS queries
3. `sniffer.py` writes MAC/IP/hostname/vendor/OS to `devices` table and domain queries to `dns_requests` table
4. Dashboard polls `/api/data` every 2 seconds and displays real-time info
5. User clicks "Get Recommendations" → calls `/api/recommend` → AI analyzes collected data → returns attack suggestions

## Running the Project

### Mock Mode vs Real Mode

WiSpy automatically detects your platform:
- **macOS** → Mock mode (uses fake data from `mock/mock_networks.py`)
- **Kali Linux** → Real mode (uses actual wireless scanner)

**Override in `.env`:**
```bash
WISPY_MOCK_MODE=true   # Force mock mode
WISPY_MOCK_MODE=false  # Force real mode
```

See `MOCK_MODE_GUIDE.md` for complete details.

### Prerequisites

**For Development (macOS):**
- Python 3.9+
- Node.js (for React frontend)

**For Production (Kali Linux):**
- **Kali Linux** (native or VirtualBox with USB passthrough)
- **TP-Link TL-WN722N** wireless adapter (Realtek RTL8188EUS chipset)
- Custom `8188eu` driver installed via DKMS (see INSTALLATION.md)
- System packages: `hostapd dnsmasq aircrack-ng iw net-tools`

### Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` file with:
```
WISPY_MOCK_MODE=true     # Optional: override auto-detection
GOOGLE_API_KEY=<your-key>
WIFI_INTERFACE=wlan0
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### Start the System

**Quick Start (Recommended):**
```bash
python start_wispy.py
```
This automatically starts both Flask backend and React frontend.

**Manual Start (Two Terminals):**

Terminal 1 - Flask Backend:
```bash
source .venv/bin/activate
python web/app.py
```

Terminal 2 - React Frontend:
```bash
cd web/frontend
npm start
```

Dashboard available at `http://localhost:3001`

**Note:** `main.py` is the OLD command-line launcher and is **not compatible** with the new React UI. Use `start_wispy.py` or the manual two-terminal approach.

### Testing
```bash
python -m pytest tests/
```

Currently only `tests/test_storage.py` exists (unit tests for SQLite layer).

## Development Guidelines

### Wireless Driver Context
**Critical:** The TP-Link TL-WN722N requires the `8188eu` driver for monitor mode. The in-kernel `rtl8xxxu` driver does NOT support monitor mode properly and must be blacklisted. If `iw dev` shows no interfaces or scanning returns zero results, check driver:
```bash
lsmod | grep rtl   # Should show ONLY 8188eu, not rtl8xxxu
```

### Security Considerations
- Flask runs as non-root user — network commands are executed via `subprocess` with explicit sudoers NOPASSWD rules
- Never run `web/app.py` as root
- All network interface manipulation (monitor mode, IP assignment, iptables) happens in `core/` modules via `subprocess.run()` with `sudo`

### Database Access Pattern
- Both processes read/write the same SQLite file concurrently
- SQLite's built-in file locking handles synchronization
- Use `upsert_device()` for partial updates — it uses `COALESCE` to never overwrite existing non-null fields
- MAC address is the primary key for devices (most reliable identifier at data link layer)

### DNS Monitoring Focus
This project **only monitors DNS traffic**. HTTP monitoring was deliberately excluded because HTTPS is ubiquitous. DNS queries remain unencrypted and reveal all services/apps a device communicates with.

### AI Recommender
- Currently planned to use Google AI Studio (Gemini)
- `analysis/recommender.py` is not yet implemented (see `plan.md`)
- Will be triggered on-demand via POST to `/api/recommend`
- Reads session summary from `get_session_summary()` and builds structured prompt

## Code Style

- Python 3
- No ORM — raw `sqlite3` module for database access
- No frontend framework — vanilla JavaScript with periodic polling
- Subprocess orchestration for all shell commands
- Keep abstractions minimal — this is a 4-week academic project, not production software

## Common Issues

| Problem | Solution |
|---------|----------|
| `hostapd: command not found` | `sudo apt install hostapd -y` |
| Scanner finds 0 networks | Driver conflict — unload `rtl8xxxu`: `sudo modprobe -r rtl8xxxu && sudo modprobe 8188eu` |
| Interface not visible in `iw dev` | Reload driver: `sudo modprobe -r 8188eu && sudo modprobe 8188eu` |
| Dashboard shows no data | Ensure `main.py` is running in Terminal 1 first |
| Permission denied errors | Check sudoers config per INSTALLATION.md Section 1.3 |

## Project Timeline

- **Phase A (Apr 30)**: Environment setup, driver config ✅
- **Phase B (May 10)**: Rogue AP deployment ✅
- **Phase C (May 30)**: Data analysis mechanism (in progress)
- **Phase D (Jun 5)**: Flask monitoring + AI recommender
- **Phase E (Jun 20)**: Final polish, documentation, demo

See `plan.md` for detailed implementation status and `README.md` for full project scope.
