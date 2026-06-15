# WiSpy — Installation Guide

## Hardware Required

- A machine running **Kali Linux** (native or VirtualBox VM)
- **TP-Link TL-WN722N v2 or v3** wireless adapter (Realtek RTL8188EUS chipset)
- If using a VM: a USB port available for passthrough

---

## Step 1 — VirtualBox USB Passthrough (VM only)

If you are running Kali inside VirtualBox, you must pass the wireless adapter directly to the VM.

1. Plug in the TP-Link adapter
2. In VirtualBox, open **Settings → USB** for your Kali VM
3. Click the **+** icon and select the entry that contains **TP-Link** or **RTL8188**
4. Start the VM
5. Verify the adapter is visible inside the VM:

```bash
lsusb
```

You should see a line like:

```
Bus 001 Device 003: ID 2357:010c TP-Link TL-WN722N v2/v3 [Realtek RTL8188EUS]
```

---

## Step 2 — Install System Packages

```bash
sudo apt update
sudo apt install -y hostapd dnsmasq aircrack-ng iw net-tools dkms git python3 python3-venv
```

---

## Step 3 — Install the Wireless Driver

Kali ships with an in-kernel `rtl8xxxu` driver that does not support monitor mode properly for this chipset. You need the custom `8188eu` driver instead.

### 3.1 Install the driver via DKMS

```bash
git clone https://github.com/aircrack-ng/rtl8188eus /tmp/rtl8188eus
cd /tmp/rtl8188eus
sudo make dkms_install
```

#### 3.1.1 Install the driver via RealTek if DKMS failed

```bash
sudo apt install -y realtek-rtl8188eus-dkms
```

### 3.2 Blacklist the conflicting in-kernel driver

```bash
echo "blacklist rtl8xxxu" | sudo tee /etc/modprobe.d/blacklist-rtl8xxxu.conf
```

### 3.3 Load the correct driver

```bash
sudo modprobe -r rtl8xxxu 2>/dev/null
sudo modprobe -r 8188eu   2>/dev/null
sudo modprobe 8188eu
```

### 3.4 Verify the interface is up

```bash
iw dev
```

You should see `wlan0` with `type managed`. If the interface is missing, try unplugging and replugging the adapter, then repeat step 3.3.

> This blacklist persists across reboots. After any kernel update run `sudo dkms autoinstall` to rebuild the driver.

---

## Step 4 — Clone the Repository

```bash
git clone <repo-url> ~/wispy
cd ~/wispy
```

---

## Step 5 — Create the Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Required Python packages (see `requirements.txt`) include:
- `scapy` (packet parsing, including TLS ClientHello metadata)
- `flask` (API server)
- `google-generativeai` (Gemini client for `/api/recommend`)
- `python-dotenv` (loading `.env` settings)

If `import flask_cors` fails when starting `web/app.py`, install it in your venv (e.g. `pip install flask-cors`).

---

## Step 6 — Configure Environment Variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env   # or edit .env directly if it already exists
nano .env
```

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com/) — required for agentic investigation and recommendations |
| `WIFI_INTERFACE` | Your wireless interface name (default: `wlan0`) — check with `iw dev` |
| `OUTBOUND_INTERFACE` | Uplink for NAT when the rogue AP is live (default: `eth0`) — check with `ip link` |
| `FLASK_HOST` | Dashboard bind address (default: `0.0.0.0`) |
| `FLASK_PORT` | Dashboard port (default: `5000`) |
| `WISPY_SNIFFER_SUDO` | Set `true` to run `core/sniffer.py` via `sudo -n` from the UI (requires passwordless sudo for your venv Python + sniffer path) |

---

## Step 7 — Verify Everything Works

Check that the adapter enters monitor mode and can see nearby networks:

```bash
sudo source .venv/bin/activate   # if not already active
sudo .venv/bin/python -c "
from core.scanner import enable_monitor_mode, scan_networks
mon = enable_monitor_mode()
nets = scan_networks(mon, duration=10)
print(f'Found {len(nets)} networks')
for n in nets: print(' ', n['ssid'])
"
```

You should see a list of nearby Wi-Fi networks.

---

## Step 8 — Run WiSpy

WiSpy uses a **Flask API** plus a **React dashboard**. Packet capture runs in `core/sniffer.py`, which writes to `data/wispy.db`.

### 8.1 Recommended — React UI

From the project root:

```bash
source .venv/bin/activate
python start_wispy.py        # starts Flask :5000 and React :3001
```

Open **http://localhost:3001**, click **Initiate scan**, pick a network, then open the monitoring screen.

> Do **not** use `main.py` with the React UI — it is the legacy CLI launcher only.

### 8.2 Kali Linux — rogue AP from the React UI

1. Set in `.env`: correct `WIFI_INTERFACE` and `OUTBOUND_INTERFACE` (usually `eth0`).
2. Configure **passwordless sudo** for the user running Flask so `core/ap_manager.py` can invoke `sudo hostapd`, `sudo dnsmasq`, `sudo ip`, `sudo iptables`, `sudo iwconfig`, etc. (see `Impl_report.md` §1.3). Paths must match your install.
3. Start the stack: `python start_wispy.py` (Flask runs as your normal user).
4. In the UI: **Initiate scan** → select target network. This calls `POST /api/select-network`, which starts `hostapd`, `dnsmasq`, and `core/sniffer.py` as background processes.
5. Connect a test client to the cloned SSID. Telemetry appears on the monitoring screen within a few seconds.

**Sniffer permissions:** `scapy.sniff()` usually requires **root** or `CAP_NET_RAW`. If flows/DNS stay empty after a client connects, run the sniffer manually in a second terminal while the AP is up:

```bash
cd ~/wispy
sudo .venv/bin/python core/sniffer.py
```

To stop the rogue AP from the API: `POST /api/stop-ap` (or exit Flask — `atexit` runs cleanup).

### 8.3 Legacy — CLI `main.py` (Kali, all-in-one terminal)

Still supported for headless lab use. Requires root:

```bash
cd ~/wispy
sudo .venv/bin/python main.py
```

Follow prompts: scan → select network → AP + sniffer start in one process tree.

### 8.4 What the sniffer captures

BPF filter (see `core/sniffer.py`):

`udp port 53 or udp port 5353 or udp port 67 or udp port 68 or tcp port 443 or tcp port 80 or tcp port 25`

| Traffic | Stored as |
|--------|-----------|
| DNS queries | `dns_requests` (ad/tracking domains filtered) |
| DNS responses | In-memory IP→hostname cache (`analysis/correlation.py`) for flow labeling |
| DHCP | `devices` (hostname, Option 55 in `dhcp_params`) |
| mDNS (`.local` services) | `mdns_broadcasts` |
| TLS ClientHello on 443 | `tls_sni`, `ja3_fingerprints` |
| TCP/UDP flows on filtered ports | `flow_sessions` (duration, bytes; `dst_host` from **SNI** or **DNS** cache, `host_source`: `sni` / `dns` / `unknown`) |
| Cleartext HTTP (80) / SMTP (25) | `plaintext_events` (method/command, host/server, captured plaintext segment in `body`) |

Flow rows are flushed to SQLite every ~5 seconds. Plaintext HTTP/SMTP uses a 60s dedup window.

### 8.5 API and dashboard surfaces

Key endpoints (`web/app.py`):

| Endpoint | Purpose |
|----------|---------|
| `GET /api/data` | Devices (with `patterns` / `flow_stats`), DNS slice, TLS, JA3, mDNS, **flows**, **plaintext** |
| `GET /api/dns`, `GET /api/flows`, `GET /api/plaintext` | Paginated feeds |
| `POST /api/start-scan`, `POST /api/select-network`, `POST /api/stop-ap` | UI workflow + real-mode AP |
| `POST /api/agent/investigate` | Agentic session investigation (Gemini) |
| `POST /api/agent/recommend`, `POST /api/recommend` | Agentic next-step suggestions (alias) |

React monitoring UI (`http://localhost:3001`): device cards, DNS table/charts, telemetry tables, **Session Reconnaissance (flows)**, **Plaintext leaks**, and **Agentic** panel (investigate vs recommend tabs).

Legacy template UI: `http://localhost:5000` (fewer extension panels).

---

## Step 9 — Privacy and Data Handling Notes

WiSpy is for **authorized lab use only**.

**Collected (metadata and selective cleartext):**

- DNS names, DHCP hostname/Option 55, mDNS service names
- TLS **SNI** and **JA3** hashes (from ClientHello only)
- **Flow sessions**: IPs, ports, timing, packet/byte counts; hostnames when inferred from SNI or recent DNS answers
- **Plaintext HTTP/SMTP** on ports 80/25 when not TLS-wrapped: request line / commands and a stored **body** field (captured segment only)

**Not collected:**

- Decrypted HTTPS/TLS application data
- MITM or credential harvesting

Operate only on networks and devices you are permitted to monitor.

---

## Step 10 — Troubleshooting

| Symptom | Fix |
|---|---|
| `sudo: hostapd: command not found` | `sudo apt install hostapd -y` |
| `iw dev` shows no wireless interface | Reload driver: `sudo modprobe -r 8188eu && sudo modprobe 8188eu` |
| Scanner finds 0 networks | Check driver with `lsmod \| grep rtl` — `rtl8xxxu` must not be listed |
| AP up but no DNS/flows | Run sniffer with sudo (§8.2); confirm client uses rogue DNS; check `data/wispy.db` |
| `Permission denied` starting AP from UI | Configure sudoers for `hostapd`, `dnsmasq`, `ip`, `iptables`, `iwconfig` (§8.2) |
| `Operation not permitted` on WiFi scan | Configure passwordless sudo for `airmon-ng`, `iw`, `ip`; grant `CAP_NET_RAW` on venv Python or include it in sudoers for `scapy.sniff()` |
| Flow host shows IP only | Normal until DNS reply or TLS SNI arrives; wait for HTTPS/DNS activity |
| TLS / JA3 / mDNS empty | Client must use 443 / mDNS on the rogue LAN |
| Plaintext panel empty | Expected on modern HTTPS-only clients; rare HTTP/SMTP cleartext only |
| Agentic buttons error | Set `GOOGLE_API_KEY` in `.env`; check Flask logs for Gemini model errors |
| React cannot reach API | Flask must be on `:5000`; frontend proxy expects port 5000 |
| DHCP leases not assigned | Check dnsmasq logs; `ip addr show wlan0` should show AP IP (e.g. `192.168.50.1`) |
| NAT works but no internet on rogue LAN | Set `OUTBOUND_INTERFACE` to your uplink (`eth0`, `wlan1`, etc.) |
