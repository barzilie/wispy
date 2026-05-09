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
| `GOOGLE_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com/) — required for AI recommendations |
| `WIFI_INTERFACE` | Your wireless interface name (default: `wlan0`) — check with `iw dev` |
| `FLASK_HOST` | Dashboard bind address (default: `0.0.0.0`) |
| `FLASK_PORT` | Dashboard port (default: `5000`) |

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

WiSpy runs as **two separate processes**. Open two terminals.

### 8.1 Optional: allow web app to run `main.py` without sudo password

If the dashboard needs to start/stop `main.py` itself, add a restricted `sudoers` rule with `visudo`.

> Replace `www-data` with the Linux user that runs your web app process.

```bash
sudo visudo
```

Add this line:

```bash
www-data ALL=(root) NOPASSWD: /home/noamb/wispy/wispy/.venv/bin/python /home/noamb/wispy/wispy/main.py
```

Then in the web app, execute `main.py` using the same absolute command via `sudo`.

```bash
sudo /home/noamb/wispy/wispy/.venv/bin/python /home/noamb/wispy/wispy/main.py
```

**Terminal 1 — Main tool (scan + rogue AP + sniffer):**

```bash
cd ~/wispy
sudo .venv/bin/python main.py
```

Follow the prompts: select a network to clone, then wait for victims to connect.

The sniffer now captures:
- DNS queries (`udp/53`)
- mDNS service broadcasts (`udp/5353`)
- DHCP metadata including Option 55 (`udp/67-68`)
- TLS ClientHello metadata on `tcp/443` (SNI and JA3 fingerprint hash)

**Terminal 2 — Dashboard:**

```bash
cd ~/wispy
source .venv/bin/activate
python web/app.py
```

Open a browser and go to `http://localhost:5000` for the **legacy** Flask template UI, or use the **React** dashboard (recommended): in another terminal run `cd web/frontend && npm start` and open `http://localhost:3001`. The React app proxies API calls to Flask on port 5000.

The JSON API (`GET /api/data`) returns devices, DNS totals, and recent rows for **TLS SNI**, **JA3**, and **mDNS** (see `web/app.py`). On macOS or when using mock mode, run `python mock_data.py` (or `python mock_data.py --reset`) to populate sample rows for all telemetry types.

---

## Privacy and Data Handling Notes

WiSpy is designed to capture **unencrypted metadata** for network analysis. With TLS telemetry enabled, the tool stores:
- TLS SNI hostnames (the requested server name in ClientHello, when present)
- JA3 hashes (fingerprint hashes derived from TLS ClientHello parameters)

It does **not** decrypt TLS payloads or capture HTTPS content bodies.

Operate WiSpy only on networks and devices you are authorized to monitor, and disclose monitoring where required by policy or law.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `sudo: hostapd: command not found` | `sudo apt install hostapd -y` |
| `iw dev` shows no wireless interface | Reload driver: `sudo modprobe -r 8188eu && sudo modprobe 8188eu` |
| Scanner finds 0 networks | Check driver with `lsmod \| grep rtl` — `rtl8xxxu` must not be listed |
| Dashboard shows nothing | Make sure `main.py` (or `core/sniffer.py`) is running in another terminal first, or load mock data with `python mock_data.py` |
| TLS / JA3 / mDNS panels empty | Normal until clients generate HTTPS (443) or mDNS (5353) traffic on the rogue segment; use `mock_data.py` to verify the UI |
| DHCP leases not assigned | Check dnsmasq output in Terminal 1; ensure `wlan0` has IP `192.168.50.1` (`ip addr show wlan0`) |
