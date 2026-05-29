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
The database evolved from a minimal **devices + DNS** design to additional telemetry tables (TLS SNI, JA3, mDNS) and a **`dhcp_params`** column on devices. The authoritative DDL and migrations live in `analysis/storage.py` (`init_db()`).

**`devices` table** — one row per connected device:

| Column | Type | Description |
|--------|------|-------------|
| `mac` | TEXT (PK) | MAC address — unique hardware identifier, used as primary key |
| `ip` | TEXT | Assigned IP address from DHCP |
| `hostname` | TEXT | Device name broadcast via DHCP (e.g. "John's iPhone") |
| `vendor` | TEXT | Manufacturer derived from MAC OUI lookup |
| `os_guess` | TEXT | Operating system inferred from TTL and DHCP fingerprint |
| `dhcp_params` | TEXT | DHCP Option 55 (parameter request list), comma-separated, when observed |
| `first_seen` | TEXT | UTC timestamp of first connection |
| `last_seen` | TEXT | UTC timestamp of most recent activity |

**`dns_requests`** — one row per stored DNS query (`id`, `device_mac`, `domain`, `timestamp`).

**`tls_sni`** — TLS ClientHello server name (`id`, `device_mac`, `sni`, `timestamp`).

**`ja3_fingerprints`** — JA3-style MD5 hash from ClientHello (`id`, `device_mac`, `ja3_hash`, `timestamp`).

**`mdns_broadcasts`** — mDNS service-style names (`id`, `device_mac`, `service_name`, `timestamp`).

See §“Telemetry Expansion” below for capture rules and indexing.

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

## 4. React Frontend Development & Multi-Screen Architecture

This phase involved migrating from the original command-line interface to a modern web-based UI with a multi-screen workflow, while maintaining the backend infrastructure.

### 4.1. Architecture Decision: Separate Frontend/Backend

**Decision:** Separate React frontend from Flask backend rather than using Flask's template engine.

**Rationale:**
- Modern development workflow with hot-reload
- Component-based architecture for maintainability
- Clear separation of concerns (API backend vs UI frontend)
- Easier to develop on macOS with mock data

**Implementation:**
- Flask backend: API-only server (`web/app.py`)
- React frontend: Standalone SPA (`web/frontend/`)
- Communication: REST API over HTTP
- CORS enabled for cross-origin requests during development

### 4.2. Multi-Screen User Flow

The original `main.py` command-line flow was replaced with a three-screen web interface:

**Screen 1: Start Screen** (`components/StartScreen/`)
- Landing page with WiSpy ASCII logo
- "INITIATE SCAN" button to begin
- Shows loading state during scan
- Warning about authorized use only

**Screen 2: Network Selection Screen** (`components/NetworkSelectionScreen/`)
- Displays all detected WiFi networks
- Shows SSID, BSSID, channel, encryption, signal strength
- Visual signal strength indicators (▰▰▰▰▰)
- Click network to select as target
- Loading overlay during AP deployment

**Screen 3: Monitoring Screen** (`components/MonitoringScreen/`)
- Real-time dashboard (original dashboard functionality)
- Device cards showing connected clients
- DNS query table
- AI attack recommendations panel
- Shows selected target network in header

### 4.3. Component Architecture

**Pattern Established:** Every component follows a 3-file structure:
- `.jsx` - Component structure (React/HTML)
- `.logic.js` - Business logic and utility functions
- `.css` - Component-specific styling

**Reasoning:**
- Clear separation of concerns
- Logic reusable and testable independently
- Consistent project structure
- Easier to navigate and maintain

**Components Created:**
- `StartScreen` - Initial landing page
- `NetworkSelectionScreen` - Network picker
- `MonitoringScreen` - Dashboard wrapper
- `Header` - App header (original, kept for consistency)
- `DeviceList` - Grid container for devices
- `DeviceCard` - Individual device display
- `DnsTable` - DNS queries table (full loaded set, infinite scroll)
- `DnsAnalytics` - DNS volume-over-time and top-domains charts (Recharts)
- `TelemetryTables` - TLS SNI, JA3, and mDNS tables (recent rows from API)
- `RecommendationsPanel` - AI recommendations UI

### 4.4. Custom React Hooks

**Created three custom hooks for state management:**

**`useAppFlow.js`:**
- Manages screen transitions (start → selection → monitoring)
- Handles WiFi scanning API call
- Handles network selection API call
- Stores selected network and networks list
- Manages loading and error states

**`useWispyData.js`:**
- Loads devices from `/api/data?include_dns=0` and the first page of DNS from `GET /api/dns`
- On each poll, refreshes **TLS SNI**, **JA3**, and **mDNS** slices from `/api/data` (`tls_sni`, `ja3`, `mdns` arrays)
- Polls every 2 seconds for device updates and incremental DNS rows (`after_id` cursor)
- Supports loading older DNS via `before_id` for infinite scroll (used by `DnsTable`)
- Exposes `dnsTotal`, `loadMoreDns`, `loadingMoreDns`, `hasMoreDns`, plus `tlsSni`, `ja3Rows`, `mdnsRows`
- Used only on monitoring screen

**`useRecommendations.js`:**
- Handles AI recommendation requests
- Manages loading state during AI processing
- Error handling for recommendation failures

**Pattern:** All data fetching logic isolated in custom hooks, components remain presentational.

### 4.5. API Endpoint Updates

**New endpoints added to `web/app.py`:**

**`POST /api/start-scan`:**
- Triggers WiFi network scanning
- Returns list of networks (mock or real based on mode)
- Stores networks in server-side state
- Returns: `{'status': 'complete', 'networks': [...], 'mock_mode': bool}`

**`POST /api/select-network`:**
- Receives selected SSID from frontend
- Stores selection in server state
- In real mode: would trigger rogue AP deployment
- Returns: `{'status': 'success', 'network': {...}}`

**`GET /api/status`:**
- Returns current system state
- Shows scanning/monitoring status
- Returns mode information (mock vs real)
- Used for debugging and monitoring

**Existing / extended endpoints:**
- `GET /api/data` — devices; optional DNS slice (`include_dns`, `dns_limit`, `dns_offset`, `dns_total`); recent **TLS SNI / JA3 / mDNS** lists with totals (`telemetry_limit`, `include_telemetry`, `*_total` fields)
- `GET /api/dns` — paginated DNS feed: `limit`, `offset`, `mac` / `device_mac`, `after_id` (newer than id), `before_id` (older than id); returns `dns`, `total`, `count`
- `POST /api/recommend` — calls `analysis.recommender.get_recommendations()` (Gemini)

### 4.6. Mock Data System Implementation

**Problem:** Need to develop UI on macOS without Kali Linux hardware.

**Solution:** Automatic platform detection with mock data system.

**Implementation:**

**`config.py`:**
- Central configuration file
- Auto-detects platform (Darwin = macOS, Linux = Kali)
- Sets `MOCK_MODE` based on platform
- Can override with `WISPY_MOCK_MODE` environment variable
- Prints startup banner showing current mode

**`mock/mock_networks.py`:**
- Contains `MOCK_NETWORKS` list
- Editable fake WiFi networks for development
- Includes realistic SSID, BSSID, channel, encryption, signal
- Easy to add/modify networks for testing different scenarios

**`mock_data.py`:**
- Populates SQLite with fake **devices** (including `dhcp_params`), **DNS**, **TLS SNI**, **JA3**, and **mDNS** rows aligned with the live sniffer schema
- `--more` appends additional DNS rows via `insert_dns`
- `--reset` wipes devices and all telemetry tables, then a normal run regenerates the full mock dataset (`--many` increases DNS count per device)

**Mode Detection Flow:**
```python
# config.py
IS_MACOS = platform.system() == 'Darwin'
MOCK_MODE = os.getenv('WISPY_MOCK_MODE', 'true' if IS_MACOS else 'false')

# web/app.py
if MOCK_MODE:
    from mock.mock_networks import get_mock_networks
else:
    from core.scanner import enable_monitor_mode, scan_networks
```

**Benefits:**
- Seamless development on macOS
- No code changes needed when deploying to Kali
- Same codebase runs in both environments
- Clear indication of current mode in logs

### 4.7. Styling: Hacker Theme Implementation

**Design Goal:** Create a cyberpunk/terminal aesthetic fitting the tool's nature.

**Theme Features:**
- Matrix green (#00ff00) on black background
- Monospace font (Courier New) throughout
- CRT screen scanline effect overlay
- Glowing text with text-shadow effects
- Terminal-style borders (no border-radius)
- Uppercase labels with letter-spacing
- Animated effects (glitch, pulse, scan)

**Key CSS Techniques:**

**Scanlines Effect:**
```css
body::before {
  content: '';
  background: repeating-linear-gradient(...);
  animation: scanlines 8s linear infinite;
}
```

**Glowing Text:**
```css
text-shadow: 
  0 0 10px rgba(0, 255, 0, 0.8),
  0 0 20px rgba(0, 255, 0, 0.6);
```

**Hover Effects:**
```css
.network-item:hover {
  box-shadow: 
    0 0 20px rgba(0, 255, 0, 0.6),
    inset 0 0 20px rgba(0, 255, 0, 0.1);
}
```

### 4.8. Development Workflow Improvements

**Problem:** Need to start both Flask backend and React frontend separately.

**Solution:** Created launcher scripts.

**`start_wispy.py`:**
- Python launcher script
- Checks dependencies (venv, npm)
- Starts Flask backend in background
- Starts React frontend
- Handles Ctrl+C gracefully (stops both)
- Cross-platform (macOS and Kali)

**`start.sh`:**
- Bash alternative to Python launcher
- Same functionality
- Executable: `chmod +x start.sh`

**Documentation Created:**
- `STARTUP_GUIDE.md` - Detailed startup instructions
- `README_STARTUP.md` - Quick TL;DR
- `MOCK_MODE_GUIDE.md` - Complete mock data documentation
- `FILES_OVERVIEW.md` - Project file navigation guide
- `COMPONENTS.md` - React component documentation

### 4.9. Port Configuration

**Issue:** Default port 3000 conflicted with Claude Code manager on macOS.

**Resolution:**
- React dev server moved to port 3001
- Configured via `.env` file in `web/frontend/`
- Flask remains on port 5000
- Dashboard URL: `http://localhost:3001`

**Configuration:**
```bash
# web/frontend/.env
PORT=3001
BROWSER=none
```

### 4.10. Current State and Limitations

**Completed Features:**
- ✅ Three-screen user flow (start → select → monitor)
- ✅ WiFi network scanning API (mock and real modes)
- ✅ Network selection and storage
- ✅ Real-time device and DNS monitoring
- ✅ Hacker-themed UI with animations
- ✅ Mock data system for development
- ✅ Auto-detection of platform
- ✅ Component-based architecture
- ✅ Custom React hooks for state management
- ✅ AI recommendations via `analysis/recommender.py` (Gemini) and extended DNS/API/dashboard features (see §7)

**Not Yet Implemented:**
- ⚠️ Actual rogue AP deployment on network selection (mock mode only)
- ⚠️ Integration between network selection and `main.py` flow
- ⚠️ Real-time status indicators on monitoring screen
- ⚠️ Network deauthentication (`core/deauth.py` exists but not integrated)

**Known Issues:**
- `main.py` is incompatible with new React UI (old command-line version)
- Network selection doesn't actually start sniffer in real mode yet
- Monitoring screen always shows mock device data regardless of mode
- No graceful error handling if wireless adapter not found in real mode

---

## 5. Next Steps

### 5.1. Backend Integration (Real Mode)

**Remaining work to make real mode functional:**

1. **Network Selection → AP Deployment:**
   - When user selects network in real mode, trigger actual AP setup
   - Call `core/ap_manager.py` functions
   - Start `hostapd` and `dnsmasq`
   - Enable routing and NAT

2. **Automatic Sniffer Start:**
   - After AP is live, automatically start `core/sniffer.py`
   - Sniffer should run as background process
   - Write captured data to SQLite (already implemented)

3. **Process Management:**
   - Track running processes (hostapd, dnsmasq, sniffer)
   - Graceful shutdown on user exit
   - Cleanup iptables rules on shutdown

### 5.2. AI Recommender Implementation

**Status:** Implemented in `analysis/recommender.py` (see §7). Remaining work is operational (valid `GOOGLE_API_KEY`, model availability) and prompt tuning if needed.

### 5.3. Error Handling and User Feedback

- Better error messages when hardware missing
- Connection status indicators on monitoring screen
- Progress feedback during AP deployment
- Validation before starting real mode operations

### 5.4. Testing

- End-to-end test on actual Kali Linux
- Verify driver compatibility
- Test rogue AP deployment
- Validate packet capture
- Confirm database writes

---

## 6. Lessons Learned

### 6.1. Separation of Concerns
The decision to separate React frontend from Flask backend proved beneficial:
- Easier development on macOS
- Cleaner code organization
- Independent testing of UI and backend
- Hot-reload during development

### 6.2. Mock Data System
Auto-detection of platform eliminated manual configuration:
- No code changes needed between environments
- Clear visibility of current mode
- Reduced development friction
- Made frontend development possible without hardware

### 6.3. Component Architecture
The 3-file component pattern (jsx/logic/css) provided:
- Clear code organization
- Reusable logic functions
- Easier testing and maintenance
- Consistent project structure

### 6.4. Custom Hooks
Isolating API logic in custom hooks:
- Simplified components (presentational only)
- Centralized data fetching logic
- Easy to modify API behavior
- Better state management

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

---

## 7. Dashboard analytics, DNS feed scaling, ad-domain filtering, and AI recommender

This phase completed the Gemini-based recommender, reduced noise from ad-tech DNS, scaled the DNS API for large logs, and enriched the React monitoring screen with per-device DNS context and charts.

### 7.1. AI recommender (`analysis/recommender.py`)

- New module invoked by `POST /api/recommend` in `web/app.py`.
- Loads `GOOGLE_API_KEY` via `config.py` (same `.env` pattern as the rest of the project).
- Builds a structured prompt from `get_session_summary()` output (JSON), framed for an authorized academic lab and defensive/educational tone.
- Uses `google.generativeai` with model fallbacks: `gemini-2.0-flash`, then `gemini-1.5-flash`, then `gemini-1.5-flash-latest`.
- Returns clear messages when the API key is missing, when there is no telemetry yet, or when all models fail.

### 7.2. Ad / ad-tech DNS filtering

- New helper module `analysis/dns_filters.py` with `is_ad_tracking_domain(domain)` backed by a compiled case-insensitive regex over common advertising and syndication host patterns (e.g. DoubleClick, Google syndication, major SSPs).
- `core/sniffer.py` calls this check in `_handle_dns` before `insert_dns`, so noisy ad lookups are not stored in `dns_requests`.
- Patterns can be extended by editing the regex fragment list in `dns_filters.py`.
- Added `tests/test_dns_filters.py` for basic allow/block checks.

### 7.3. Storage and API changes for DNS and multi-protocol telemetry (`analysis/storage.py`, `web/app.py`)

- Shared helpers `_fetch_telemetry` / `_count_telemetry` (whitelist: `dns_requests`, `tls_sni`, `ja3_fingerprints`, `mdns_broadcasts`) drive consistent newest-first cursor pagination.
- `get_dns_requests` / `count_dns_requests` plus **`get_tls_sni`**, **`get_ja3`**, **`get_mdns`** and matching **`count_*`** (same `limit` / `offset` / `device_mac` / `after_id` / `before_id` semantics as DNS).
- Index `idx_dns_device_mac` on `dns_requests(device_mac)` for per-device queries.
- `get_session_summary()` pulls large DNS, TLS, JA3, and mDNS slices and emits per-device fields: `domains_queried`, `tls_sni`, `ja3_fingerprints`, `mdns_services`, and `dhcp_params`, for richer Gemini prompts.

**Flask:**

- `GET /api/data` — optional `include_dns`, `dns_limit`, `dns_offset`, `dns_total`; optional **`include_telemetry`**, **`telemetry_limit`**, with **`tls_sni`**, **`tls_sni_total`**, **`ja3`**, **`ja3_total`**, **`mdns`**, **`mdns_total`**.
- `GET /api/dns` — dedicated DNS listing with pagination/cursor parameters and JSON metadata (`total`, `count`).

### 7.4. React monitoring UI updates (`web/frontend`)

- **`useWispyData.js`:** Initial parallel fetch of `GET /api/dns` (first page) and `GET /api/data?include_dns=0`; polling updates devices, TLS/JA3/mDNS arrays from `/api/data`, and merges new DNS via `after_id`; supports “cold start” when the DB gains rows after an empty first load; tracks end-of-history for older DNS pages.
- **`TelemetryTables`:** Three scrollable tables for recent TLS SNI, JA3, and mDNS rows (styled consistently with `DnsTable`).
- **`DnsTable`:** Renders all loaded DNS rows; uses an `IntersectionObserver` sentinel to call `loadMoreDns`; header shows `loaded of total` when more DB rows exist.
- **`DnsAnalytics`:** Queries per minute (line chart) and top domains (bar chart) via **`recharts`**.
- **`DeviceCard` / `DeviceList`:** **DHCP Option 55** when `dhcp_params` is set; per-device previews for **DNS**, **SNI**, **JA3**, and **mDNS** from the loaded API slices.
- **`RecommendationsPanel`:** Displays hook-level errors via an `error` prop and CSS class `recommendations-error`.

### 7.5. Verification

- Frontend production build (`npm run build`) succeeded with Recharts bundled.
- `tests/test_dns_filters.py` runs without importing the full storage stack (avoids `dotenv` in minimal environments).

### 7.6. Operator notes

- Set **`GOOGLE_API_KEY`** in `.env` for live Gemini recommendations.
- **Legacy Flask template** (`web/templates/index.html` + `web/static/js/app.js`) calls `GET /api/data` and renders **DNS**, **TLS SNI**, **JA3**, and **mDNS** sections plus DHCP Option 55 on device cards when present.
- **`mock_data.py`** seeds all of the above for offline UI testing; see `MOCK_MODE_GUIDE.md`.

### 7.7. Cross-reference

- End-to-end capture behavior and BPF filter: **§“Telemetry Expansion”** (duplicate §4 heading in this document) and `INSTALLATION.md` Step 8.
- File map: `FILES_OVERVIEW.md`.

---

## 8. TA feedback extension (session recon, plaintext, agentic)

Implemented per [`extension.md`](extension.md) in three tracks.

### 8.1. Track 1 — Session reconnaissance

**Database (`analysis/storage.py`):**

- Table `flow_sessions`: `device_mac`, `proto`, `src_ip`, `dst_ip`, `dst_port`, `dst_host`, `host_source` (`sni` | `dns` | `unknown`), `first_seen`, `last_seen`, `packet_count`, `byte_count`, `service_label`.
- Indexes: `idx_flows_device_last_seen`, `idx_flows_dst_ip`.
- `upsert_flow_session()` merges rows for the same 5-tuple within a 60s idle window (accumulates packets/bytes; prefers non-unknown `dst_host` / `host_source`).
- Pagination via `_TELEMETRY_TABLES`: `get_flow_sessions()`, `count_flow_sessions()`.

**DNS correlation (`analysis/correlation.py`):**

- In-memory `(device_mac, ip) → (domain, timestamp)` cache, 15-minute TTL.
- Sniffer feeds cache from DNS responses (`QR=1`); flows call `resolve_ip_to_host()` when SNI is absent.

**Sniffer (`core/sniffer.py`):**

- Active flow table with periodic flush to SQLite.
- TLS SNI preferred for `host_source`; DNS cache as fallback.

**Patterns (`analysis/patterns.py`):**

- `analyze_device_patterns(device_mac)` — heuristics: plaintext leaks, social/work/media tags, background sync.

**API:** `GET /api/flows`, `flows` / `flows_total` on `GET /api/data`.

### 8.2. Track 2 — Plaintext packet hunting

**Database:** table `plaintext_events` — `proto` (`http` | `smtp`), `host_or_server`, `method_or_command`, `body` (full captured plaintext segment), `timestamp`.

**Sniffer:** BPF includes `tcp port 80` and `tcp port 25`; parsers extract HTTP request line / `Host` and SMTP banner/commands; 60s dedup window.

**API:** `GET /api/plaintext`, `plaintext` / `plaintext_total` on `GET /api/data`.

### 8.3. Track 3 — Agentic module

**Package `analysis/agentic/`:**

- `client.py` — Gemini config and model fallbacks.
- `context.py` — `build_agent_context()` from devices, DNS, flows, plaintext, patterns.
- `prompts/investigate.py` — session investigation (lab analysis focus).
- `prompts/recommend.py` — next-step / vulnerability suggestions (educational framing).

**API:** `POST /api/agent/investigate`, `POST /api/agent/recommend`; `/api/recommend` retained as alias.

[`analysis/recommender.py`](analysis/recommender.py) delegates to the agentic package.

### 8.4. React dashboard integration

- [`useWispyData.js`](web/frontend/src/hooks/useWispyData.js) polls `flows` and `plaintext` from `/api/data`.
- [`FlowAnalytics`](web/frontend/src/components/FlowAnalytics/) — flow table with SNI/DNS resolution badges.
- [`PlaintextPanel`](web/frontend/src/components/PlaintextPanel/) — cleartext leaks with expandable bodies.
- [`AgenticPanel`](web/frontend/src/components/AgenticPanel/) — wraps tabbed investigation / recommend UI; [`useRecommendations.js`](web/frontend/src/hooks/useRecommendations.js) calls both agent endpoints.

### 8.5. Real-mode process management

[`web/app.py`](web/app.py): on `POST /api/select-network` (non-mock), disables monitor mode, configures interface, starts `hostapd` / `dnsmasq`, spawns `core/sniffer.py` with project `cwd`. `atexit` and `POST /api/stop-ap` invoke `cleanup_ap_processes()` → `ap_manager.teardown()`.

### 8.6. Verification

```bash
python -m unittest tests/test_extension.py
python mock_data.py --reset && python mock_data.py
python start_wispy.py
```

Manual: monitoring screen shows flows, plaintext panel, and both agentic tabs on `http://localhost:3001`.