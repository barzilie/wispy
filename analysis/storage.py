import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DB_PATH = os.path.join(PROJECT_ROOT, "data", "wispy.db")


def _connect():
    """Opens a connection to the SQLite database, creating the data directory if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Creates and migrates telemetry tables. Safe to call on every startup."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                mac        TEXT PRIMARY KEY,
                ip         TEXT,
                hostname   TEXT,
                vendor     TEXT,
                os_guess   TEXT,
                dhcp_params TEXT,
                first_seen TEXT,
                last_seen  TEXT
            )
        """)
        # Backfill new columns on existing installations.
        cols = conn.execute("PRAGMA table_info(devices)").fetchall()
        col_names = {row[1] for row in cols}
        if "dhcp_params" not in col_names:
            conn.execute("ALTER TABLE devices ADD COLUMN dhcp_params TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_requests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac TEXT,
                domain     TEXT,
                timestamp  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tls_sni (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac TEXT,
                sni        TEXT,
                timestamp  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ja3_fingerprints (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac TEXT,
                ja3_hash   TEXT,
                timestamp  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mdns_broadcasts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac   TEXT,
                service_name TEXT,
                timestamp    TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tls_sni_device_ts ON tls_sni(device_mac, timestamp)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ja3_device_ts ON ja3_fingerprints(device_mac, timestamp)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mdns_device_ts ON mdns_broadcasts(device_mac, timestamp)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mdns_service_name ON mdns_broadcasts(service_name)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tls_sni_value ON tls_sni(sni)"
        )
        conn.commit()


def upsert_device(mac, ip=None, hostname=None, vendor=None, os_guess=None, dhcp_params=None):
    """Inserts a new device or updates an existing one. Only non-None fields overwrite stored values,
    so partial updates from different sources (sniffer, fingerprinter) never erase each other."""
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        existing = conn.execute(
            "SELECT first_seen FROM devices WHERE mac = ?", (mac,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE devices
                SET ip=COALESCE(?,ip), hostname=COALESCE(?,hostname),
                    vendor=COALESCE(?,vendor), os_guess=COALESCE(?,os_guess),
                    dhcp_params=COALESCE(?,dhcp_params),
                    last_seen=?
                WHERE mac=?
            """, (ip, hostname, vendor, os_guess, dhcp_params, now, mac))
        else:
            conn.execute("""
                INSERT INTO devices (mac, ip, hostname, vendor, os_guess, dhcp_params, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (mac, ip, hostname, vendor, os_guess, dhcp_params, now, now))
        conn.commit()


def insert_dns(device_mac, domain):
    """Records a single DNS query made by a device."""
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO dns_requests (device_mac, domain, timestamp) VALUES (?, ?, ?)",
            (device_mac, domain, now)
        )
        conn.commit()


def insert_tls_sni(device_mac, sni):
    """Records a TLS SNI value observed from a client hello."""
    if not sni:
        return
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO tls_sni (device_mac, sni, timestamp) VALUES (?, ?, ?)",
            (device_mac, sni, now)
        )
        conn.commit()


def insert_ja3(device_mac, ja3_hash):
    """Records a JA3 fingerprint hash observed from a client hello."""
    if not ja3_hash:
        return
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO ja3_fingerprints (device_mac, ja3_hash, timestamp) VALUES (?, ?, ?)",
            (device_mac, ja3_hash, now)
        )
        conn.commit()


def insert_mdns(device_mac, service_name):
    """Records an mDNS service name."""
    if not service_name:
        return
    now = datetime.utcnow().isoformat()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO mdns_broadcasts (device_mac, service_name, timestamp) VALUES (?, ?, ?)",
            (device_mac, service_name, now)
        )
        conn.commit()


def get_devices():
    """Returns all tracked devices as a list of dicts, ordered by most recently seen."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM devices ORDER BY last_seen DESC").fetchall()
    return [dict(r) for r in rows]


def get_dns_requests(limit=100):
    """Returns the most recent DNS queries up to the given limit, ordered newest first."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM dns_requests ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def reset_db():
    """Deletes all data from telemetry tables after user confirmation."""
    confirm = input("This will delete ALL data from the database. Type 'yes' to confirm: ")
    if confirm.strip().lower() != 'yes':
        print("Reset cancelled.")
        return
    with _connect() as conn:
        conn.execute("DELETE FROM devices")
        conn.execute("DELETE FROM dns_requests")
        conn.execute("DELETE FROM tls_sni")
        conn.execute("DELETE FROM ja3_fingerprints")
        conn.execute("DELETE FROM mdns_broadcasts")
        conn.execute(
            "DELETE FROM sqlite_sequence WHERE name IN ('dns_requests', 'tls_sni', 'ja3_fingerprints', 'mdns_broadcasts')"
        )
        conn.commit()
    print("Database reset.")


def get_session_summary():
    """Returns a compact summary for the AI recommender."""
    devices = get_devices()
    dns = get_dns_requests(limit=500)

    summary = []
    for device in devices:
        mac = device["mac"]
        domains = [r["domain"] for r in dns if r["device_mac"] == mac]
        summary.append({
            "mac": mac,
            "ip": device["ip"],
            "hostname": device["hostname"],
            "vendor": device["vendor"],
            "os_guess": device["os_guess"],
            "domains_queried": list(set(domains)),
        })
    return summary




