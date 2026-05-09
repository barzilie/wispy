#!/usr/bin/env python3
"""
Mock data generator for WiSpy dashboard development on macOS.
Populates the SQLite database with realistic fake devices and DNS queries.

Usage:
    python mock_data.py          # Generate fresh mock data
    python mock_data.py --more   # Add more queries to existing data
    python mock_data.py --reset  # Clear all data first
"""

import random
import sys
from datetime import datetime, timedelta
from analysis.storage import init_db, upsert_device, insert_dns, reset_db

# Realistic device profiles
MOCK_DEVICES = [
    {
        "mac": "a4:83:e7:12:34:56",
        "ip": "192.168.50.10",
        "hostname": "Johns-iPhone",
        "vendor": "Apple",
        "os_guess": "iOS",
        "domains": [
            "api.instagram.com", "graph.instagram.com", "www.instagram.com",
            "api.twitter.com", "mobile.twitter.com",
            "www.whatsapp.net", "web.whatsapp.com",
            "outlook.office365.com", "login.microsoftonline.com",
            "www.youtube.com", "i.ytimg.com",
            "www.reddit.com", "oauth.reddit.com",
        ]
    },
    {
        "mac": "dc:a6:32:ab:cd:ef",
        "ip": "192.168.50.11",
        "hostname": "DESKTOP-8H3KL2",
        "vendor": "Dell",
        "os_guess": "Windows 10",
        "domains": [
            "www.office.com", "outlook.office365.com", "login.live.com",
            "www.microsoft.com", "update.microsoft.com",
            "store.steampowered.com", "steamcommunity.com",
            "discord.com", "gateway.discord.gg",
            "www.twitch.tv", "api.twitch.tv",
            "github.com", "api.github.com",
            "stackoverflow.com",
        ]
    },
    {
        "mac": "f8:0f:41:98:76:54",
        "ip": "192.168.50.12",
        "hostname": "MacBook-Pro",
        "vendor": "Apple",
        "os_guess": "macOS",
        "domains": [
            "api.twitter.com", "abs.twimg.com",
            "api.slack.com", "slack.com",
            "www.notion.so", "api.notion.com",
            "zoom.us", "api.zoom.us",
            "mail.google.com", "calendar.google.com", "drive.google.com",
            "www.figma.com", "api.figma.com",
            "www.spotify.com", "api.spotify.com",
        ]
    },
    {
        "mac": "b8:27:eb:11:22:33",
        "ip": "192.168.50.13",
        "hostname": "raspberrypi",
        "vendor": "Raspberry Pi Foundation",
        "os_guess": "Linux",
        "domains": [
            "archive.raspberrypi.org",
            "downloads.raspberrypi.org",
            "api.github.com", "github.com",
            "pypi.org", "files.pythonhosted.org",
            "hub.docker.com", "registry-1.docker.io",
        ]
    },
    {
        "mac": "e4:5f:01:aa:bb:cc",
        "ip": "192.168.50.14",
        "hostname": "Galaxy-S21",
        "vendor": "Samsung",
        "os_guess": "Android",
        "domains": [
            "android.googleapis.com", "play.google.com",
            "www.tiktok.com", "api.tiktok.com",
            "api.snapchat.com", "app.snapchat.com",
            "www.facebook.com", "graph.facebook.com",
            "api.spotify.com", "spclient.wg.spotify.com",
            "www.netflix.com", "api-global.netflix.com",
        ]
    },
]


def generate_mock_data(num_queries_per_device=15):
    """Generate realistic mock data for dashboard testing."""
    init_db()

    print("[*] Generating mock devices and DNS queries...\n")

    now = datetime.utcnow()

    for device in MOCK_DEVICES:
        # Insert device first
        first_seen = now - timedelta(minutes=random.randint(5, 60))
        upsert_device(
            mac=device["mac"],
            ip=device["ip"],
            hostname=device["hostname"],
            vendor=device["vendor"],
            os_guess=device["os_guess"]
        )

        print(f"[+] Device: {device['hostname']} ({device['mac']}) - {device['vendor']} {device['os_guess']}")

        # Generate DNS queries with realistic timing
        # We'll directly insert into DB with custom timestamps
        import sqlite3
        import os

        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "wispy.db")
        conn = sqlite3.connect(db_path)

        domains = device["domains"]
        for i in range(num_queries_per_device):
            domain = random.choice(domains)
            # Queries spread over the last hour
            query_time = first_seen + timedelta(minutes=random.randint(0, 55))

            conn.execute(
                "INSERT INTO dns_requests (device_mac, domain, timestamp) VALUES (?, ?, ?)",
                (device["mac"], domain, query_time.isoformat())
            )

        conn.commit()
        conn.close()

        print(f"    └─ Generated {num_queries_per_device} DNS queries")

    print(f"\n[+] Mock data generated successfully!")
    print(f"[+] Total devices: {len(MOCK_DEVICES)}")
    print(f"[+] Total DNS queries: {len(MOCK_DEVICES) * num_queries_per_device}")
    print(f"\n[*] Start the dashboard with: python web/app.py")


def add_more_queries(num_additional=10):
    """Add more DNS queries to existing devices for testing real-time updates."""
    print(f"[*] Adding {num_additional} more queries per device...\n")

    for device in MOCK_DEVICES:
        for i in range(num_additional):
            domain = random.choice(device["domains"])
            insert_dns(device["mac"], domain)
        print(f"[+] Added {num_additional} queries for {device['hostname']}")

    print(f"\n[+] Additional queries added. Refresh your dashboard to see updates.")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        print("[!] Resetting database...")
        # Skip confirmation for automation
        import analysis.storage as storage
        with storage._connect() as conn:
            conn.execute("DELETE FROM devices")
            conn.execute("DELETE FROM dns_requests")
            conn.commit()
        print("[+] Database reset complete.\n")

    if "--more" in sys.argv:
        add_more_queries(num_additional=20)
    else:
        num_queries = 25 if "--many" in sys.argv else 15
        generate_mock_data(num_queries_per_device=num_queries)
