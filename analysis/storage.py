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
    """Creates the devices and dns_requests tables if they don't already exist. Safe to call on every startup."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                mac        TEXT PRIMARY KEY,
                ip         TEXT,
                hostname   TEXT,
                vendor     TEXT,
                os_guess   TEXT,
                first_seen TEXT,
                last_seen  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_requests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac TEXT,
                domain     TEXT,
                timestamp  TEXT
            )
        """)
        conn.commit()


def upsert_device(mac, ip=None, hostname=None, vendor=None, os_guess=None):
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
                    last_seen=?
                WHERE mac=?
            """, (ip, hostname, vendor, os_guess, now, mac))
        else:
            conn.execute("""
                INSERT INTO devices (mac, ip, hostname, vendor, os_guess, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (mac, ip, hostname, vendor, os_guess, now, now))
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
    """Deletes all data from devices and dns_requests after user confirmation."""
    confirm = input("This will delete ALL data from the database. Type 'yes' to confirm: ")
    if confirm.strip().lower() != 'yes':
        print("Reset cancelled.")
        return
    with _connect() as conn:
        conn.execute("DELETE FROM devices")
        conn.execute("DELETE FROM dns_requests")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('dns_requests')")
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




