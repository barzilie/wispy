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

---

## 4. Telemetry Expansion (TLS SNI, mDNS, DHCP Option 55, JA3)

This phase expanded WiSpy from DNS-focused telemetry to multi-protocol metadata capture while preserving backward compatibility with existing database files.

### 4.1. Storage Layer Migration and Schema Extension
The storage module in use by the sniffer is `analysis/storage.py` (imported by `core/sniffer.py`), so all persistence changes were implemented there.

#### 4.1.1 `devices` table migration
The `devices` table was extended with:
- `dhcp_params` (TEXT): stores DHCP Option 55 parameter request list as a comma-separated string.

To avoid breaking existing deployments:
- `init_db()` continues using `CREATE TABLE IF NOT EXISTS`.
- A runtime migration check was added via `PRAGMA table_info(devices)`.
- If `dhcp_params` is missing, `ALTER TABLE devices ADD COLUMN dhcp_params TEXT` is executed.

#### 4.1.2 New telemetry tables
Three new tables were added:

1. **`tls_sni`**
   - `id` (INTEGER PK AUTOINCREMENT)
   - `device_mac` (TEXT)
   - `sni` (TEXT)
   - `timestamp` (TEXT)

2. **`ja3_fingerprints`**
   - `id` (INTEGER PK AUTOINCREMENT)
   - `device_mac` (TEXT)
   - `ja3_hash` (TEXT)
   - `timestamp` (TEXT)

3. **`mdns_broadcasts`**
   - `id` (INTEGER PK AUTOINCREMENT)
   - `device_mac` (TEXT)
   - `service_name` (TEXT)
   - `timestamp` (TEXT)

#### 4.1.3 Insert APIs and upsert updates
Added insert helpers:
- `insert_tls_sni(device_mac, sni)`
- `insert_ja3(device_mac, ja3_hash)`
- `insert_mdns(device_mac, service_name)`

Updated `upsert_device(...)` to accept `dhcp_params` and preserve non-null existing values using SQL `COALESCE`, consistent with the existing partial-update strategy.

Updated `reset_db()` to clear all telemetry tables and reset related SQLite sequences.

### 4.2. Sniffer Expansion and Protocol Parsing
`core/sniffer.py` was expanded with protocol-specific handlers and routing logic.

#### 4.2.1 BPF scope increase
The packet filter was widened from DNS+DHCP only to:

`udp port 53 or udp port 5353 or udp port 67 or udp port 68 or tcp port 443`

This enables capture for:
- DNS (`53`)
- mDNS (`5353`)
- DHCP (`67/68`)
- TLS metadata on HTTPS (`443`)

#### 4.2.2 DHCP Option 55 capture
The DHCP handler now parses:
- `hostname`
- `param_req_list` (Option 55)

Option 55 values are normalized into a comma-separated string and persisted to `devices.dhcp_params`.

#### 4.2.3 mDNS capture
An mDNS handler was added to process `UDP/5353` packets containing DNS layers and extract:
- query names (`qname`)
- resource record names (`rrname`)

Noise filtering rules:
- keep only `.local` names
- require `_` in the name to focus on service-style records (for example `_airplay._tcp.local`)

Captured names are inserted into `mdns_broadcasts`.

#### 4.2.4 TLS ClientHello metadata
TLS parsing was added using `scapy.layers.tls` (import guarded with fallback when TLS layer is unavailable).

For each TLS ClientHello on `TCP/443`:
- extract SNI from extension type `0` and store in `tls_sni`
- derive JA3-style input from version/ciphers/extensions/curves/point formats
- hash with MD5 and store in `ja3_fingerprints`

### 4.3. Deduplication and Rate Limiting Strategy
To reduce event storms from repeated broadcasts/handshakes, in-memory time-window deduplication was implemented in `core/sniffer.py`:

- `MDNS_DEDUP_WINDOW_SEC` (default: `120`)
- `TLS_SNI_DEDUP_WINDOW_SEC` (default: `300`)
- `JA3_DEDUP_WINDOW_SEC` (default: `300`)

Dedup keys:
- mDNS: `(device_mac, service_name)`
- SNI: `(device_mac, sni)`
- JA3: `(device_mac, ja3_hash)`

Implementation detail:
- A shared `_should_emit(...)` helper checks last-seen timestamps in process memory.
- Events observed again within the configured window are skipped.

Important correction made during this phase:
- Initial mDNS duplicate prevention in the DB layer suppressed repeats indefinitely.
- This was replaced with time-window suppression in the sniffer, preserving long-term telemetry while reducing short-term noise.

### 4.4. Database Indexing for Query Performance
Added indexes in `init_db()` using `CREATE INDEX IF NOT EXISTS`:

- `idx_tls_sni_device_ts` on `tls_sni(device_mac, timestamp)`
- `idx_ja3_device_ts` on `ja3_fingerprints(device_mac, timestamp)`
- `idx_mdns_device_ts` on `mdns_broadcasts(device_mac, timestamp)`
- `idx_mdns_service_name` on `mdns_broadcasts(service_name)`
- `idx_tls_sni_value` on `tls_sni(sni)`

These support common dashboard/API access patterns by device timeline and metadata lookup.

### 4.5. Operational Documentation Updates
`INSTALLATION.md` was updated to reflect the expanded telemetry behavior:

- Added dependency notes for `scapy` and `python-dotenv`
- Documented expanded capture scope (DNS, mDNS, DHCP Option 55, TLS ClientHello metadata)
- Added privacy/data handling guidance for TLS metadata collection:
  - SNI and JA3 hash are stored
  - TLS payloads are not decrypted
  - usage must be limited to authorized environments

### 4.6. Verification Steps Executed
Post-change validation performed:
- Python syntax compilation:
  - `python3 -m py_compile analysis/storage.py core/sniffer.py`
- Lint/diagnostic pass on edited files:
  - no linter errors reported

Known environment limitation encountered during runtime smoke test:
- `python-dotenv` was missing in the execution environment (`ModuleNotFoundError: dotenv`) when attempting a direct `init_db()` runtime invocation; this is an environment dependency issue, not a syntax/integration issue in the code changes.