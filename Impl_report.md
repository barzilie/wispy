# Project WiSpy: Implementation Report

## 1. Initial Environment Setup and Configuration

Before commencing the development of the data interception and monitoring modules, a robust and secure foundational environment was established. This phase was critical to ensure that the hardware and software components could interact seamlessly without compromising the host system's integrity.

### 1.1. Virtualization and Hardware Integration
The project was deployed within a Kali Linux virtual machine hosted on VirtualBox. To enable the virtualized environment to interact with the physical wireless spectrum, explicit hardware passthrough was configured:
* **USB Passthrough:** The TP-Link TL-WN722N wireless adapter was mapped directly to the Kali Linux guest OS. This bypassed the hypervisor's default network abstraction, allowing the guest OS to recognize the adapter as a physical wireless interface (`wlan0`) rather than a generic Ethernet controller.

### 1.2. Wireless Adapter Driver Configuration
To support Phase A's requirement for environmental mapping and packet sniffing, the wireless adapter required configuration to operate in "Monitor Mode."
* **Chipset Verification:** The TP-Link TL-WN722N adapter's hardware revision was identified to determine the underlying chipset (Atheros for V1, Realtek for V2/V3).
* **Driver Installation:** For Realtek-based revisions, the native drivers were insufficient for packet injection and monitor mode. The custom `rtl8188eus` driver was compiled and loaded into the Linux kernel using `dkms` (Dynamic Kernel Module Support).
* **Interface State Management:** Utility scripts were created using `airmon-ng` and `iw` to reliably transition the interface between *Managed* mode (for standard connectivity) and *Monitor* mode (for 802.11 frame interception).

### 1.3. Security and Permission Management (Least Privilege Principle)
A core architectural requirement was integrating low-level network manipulation (requiring `root` privileges) with a Flask-based web dashboard. Running a web application as a superuser introduces significant security vulnerabilities. To mitigate this:
* **Dedicated Execution User:** The Flask application was configured to run under a standard, non-root user account.
* **Sudoers Configuration:** The `/etc/sudoers` file was explicitly modified to grant the application user precise, passwordless execution rights (`NOPASSWD`) strictly limited to the required networking binaries (e.g., `/usr/sbin/airmon-ng`, `/usr/sbin/ip`, `/usr/sbin/iw`). This adheres to the principle of least privilege, ensuring the dashboard can orchestrate network state changes without exposing the entire OS to root-level exploits.

### 1.4. Development Environment Preparation
To maintain dependency isolation and ensure reproducibility, the Python development environment was structured as follows:
* **Virtual Environment (venv):** A dedicated Python virtual environment was initialized to encapsulate the project's dependencies.
* **Core Dependencies:**
    * `scapy`: Installed for low-level packet crafting, sniffing, and DNS request monitoring.
    * `Flask`: Configured to serve the local dashboard and handle API requests.
    * `google-generativeai`: Integrated for AI-powered attack recommendation generation via Google AI Studio (Gemini).
    * `python-dotenv`: Used to manage environment variables (API keys, interface name, paths) from a `.env` file.
* **Subprocess Orchestration:** Python's `subprocess` module was established as the standard method for executing the underlying bash commands and networking tools, allowing the backend to capture standard output/error streams in real-time and handle execution state dynamically.

---

## 2. Data Layer — Persistent Storage Design

### 2.1. Database Selection
SQLite was selected as the persistence layer for its simplicity and zero-configuration nature. Unlike client-server databases such as PostgreSQL or MySQL, SQLite operates as a single file on disk (`data/wispy.db`), requiring no daemon, no user management, and no network port. Access control is handled entirely by Linux file system permissions on the Kali host.

Python's built-in `sqlite3` module was used directly, with no ORM or additional abstraction layer, keeping the dependency footprint minimal.

### 2.2. Process Architecture
The system runs as two independent processes:
* **Terminal 1:** `python core/sniffer.py` — captures packets and writes to the database.
* **Terminal 2:** `python web/app.py` — serves the dashboard and reads from the database.

Both processes access the same SQLite file concurrently. SQLite's built-in file locking handles concurrent reads and writes safely without any additional synchronization.

### 2.3. Schema Design
Two tables were designed to capture all relevant monitoring data:

**`devices` table** — one row per connected device:

| Column | Type | Description |
|--------|------|-------------|
| `mac` | TEXT (PK) | MAC address — unique hardware identifier, used as primary key |
| `ip` | TEXT | Assigned IP address from DHCP |
| `hostname` | TEXT | Device name broadcast via DHCP (e.g. "John's iPhone") |
| `vendor` | TEXT | Manufacturer derived from MAC OUI lookup |
| `os_guess` | TEXT | Operating system inferred from TTL and DHCP fingerprint |
| `first_seen` | TEXT | UTC timestamp of first connection |
| `last_seen` | TEXT | UTC timestamp of most recent activity |

**`dns_requests` table** — one row per DNS query:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER (PK) | Auto-incrementing row ID |
| `device_mac` | TEXT | Foreign key linking query to a device |
| `domain` | TEXT | Domain name queried (e.g. "api.instagram.com") |
| `timestamp` | TEXT | UTC timestamp of the query |

### 2.4. Key Implementation Decisions
* **MAC as primary key:** Every network packet contains the source MAC address, making it the most reliable and consistent device identifier available at the data link layer.
* **Partial updates with COALESCE:** The `upsert_device` function uses SQL `COALESCE` so that different sources (sniffer, fingerprinter) can enrich a device record independently without overwriting each other's data.
* **Absolute path resolution:** The database path is resolved relative to the project root using `__file__`, ensuring the DB is always created in `data/wispy.db` regardless of the working directory from which the script is launched.
* **DNS focus:** HTTP traffic monitoring was deliberately excluded. With the near-universal adoption of HTTPS, HTTP-layer inspection yields minimal useful data. DNS queries, however, remain unencrypted and reveal the full set of services and applications a device communicates with.

---

## 3. System Integration and Debugging

### 3.1. AP Daemon Installation
During the first full end-to-end run of `main.py`, the rogue AP failed to start with the error `sudo: hostapd: command not found`. Although `hostapd` is a standard Kali Linux tool, it was not present in the base VM image. It was installed via:

```bash
sudo apt install hostapd -y
```

After installation, `start_hostapd()` in `core/ap_manager.py` launched successfully.

### 3.2. Wireless Driver Conflict Resolution
The beacon scanner (`core/scanner.py`) returned zero results despite the interface appearing to be in monitor mode. Investigation revealed a driver conflict: two kernel modules were loaded simultaneously for the same physical adapter:

* **`rtl8xxxu`** — the in-kernel Realtek driver, loaded by default at boot
* **`8188eu`** — the custom `rtl8188eus` driver installed via `dkms`, required for reliable monitor mode and packet capture

Because `rtl8xxxu` loaded first and claimed `wlan0`, it took precedence. This driver has known limitations with monitor mode on this chipset — beacon frames were not delivered to userspace, causing `scapy.sniff()` to capture nothing.

**Resolution:** The in-kernel driver was unloaded and permanently blacklisted:

```bash
sudo modprobe -r rtl8xxxu
echo "blacklist rtl8xxxu" | sudo tee /etc/modprobe.d/blacklist-rtl8xxxu.conf
sudo modprobe -r 8188eu && sudo modprobe 8188eu
```

After reloading `8188eu`, the `wlan0` interface reappeared under the correct driver and beacon frame capture functioned correctly.

### 3.3. Scanner Validation
With the correct driver active, `core/scanner.py` successfully sniffed 802.11 beacon frames across all 2.4 GHz channels via the built-in channel-hopping thread, identified nearby networks, and returned them for user selection. The full `main.py` flow — monitor mode → scan → network selection → AP configuration → hostapd + dnsmasq startup → sniffer — executed end-to-end without errors.