#!/usr/bin/env python3
"""
fills sqlite with fake devices/dns for testing on mac
usage:
    python mock_data.py          # fresh data
    python mock_data.py --more   # more dns rows
    python mock_data.py --reset  # wipe first
"""

import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

from analysis.storage import init_db, upsert_device, insert_dns

# fake device profiles - tweak domains/sni per device type
MOCK_DEVICES = [
    {
        "mac": "a4:83:e7:12:34:56",
        "ip": "192.168.50.10",
        "hostname": "Johns-iPhone",
        "vendor": "Apple",
        "os_guess": "iOS",
        "dhcp_params": "1,3,6,15,28,119,121",
        "domains": [
            "api.instagram.com", "graph.instagram.com", "www.instagram.com",
            "api.twitter.com", "mobile.twitter.com",
            "www.whatsapp.net", "web.whatsapp.com",
            "outlook.office365.com", "login.microsoftonline.com",
            "www.youtube.com", "i.ytimg.com",
            "www.reddit.com", "oauth.reddit.com",
        ],
        "sni_hosts": [
            "api.instagram.com", "graph.instagram.com", "gateway.icloud.com",
            "courier.push.apple.com", "www.youtube.com",
        ],
        "ja3_samples": [
            "e7d705a3286e1ea8e910c2f49a1a4d4f",
            "6734f37431670b3b4304d8336672b22d",
        ],
        "mdns_services": [
            "_sleep-proxy._udp.local",
            "_companion-link._tcp.local",
            "_rdlink._tcp.local",
        ],
    },
    {
        "mac": "dc:a6:32:ab:cd:ef",
        "ip": "192.168.50.11",
        "hostname": "DESKTOP-8H3KL2",
        "vendor": "Dell",
        "os_guess": "Windows 10",
        "dhcp_params": "1,15,3,6,44,46,47,31,33,121,249,252",
        "domains": [
            "www.office.com", "outlook.office365.com", "login.live.com",
            "www.microsoft.com", "update.microsoft.com",
            "store.steampowered.com", "steamcommunity.com",
            "discord.com", "gateway.discord.gg",
            "www.twitch.tv", "api.twitch.tv",
            "github.com", "api.github.com",
            "stackoverflow.com",
        ],
        "sni_hosts": [
            "www.microsoft.com", "login.live.com", "discord.com",
            "api.github.com", "store.steampowered.com",
        ],
        "ja3_samples": [
            "a0e9f5d64349fb13191bc781f81f42e1",
            "51c74c2e95f6b77e7b72c3a4a45f5b36",
        ],
        "mdns_services": [
            "_googlecast._tcp.local",
        ],
    },
    {
        "mac": "f8:0f:41:98:76:54",
        "ip": "192.168.50.12",
        "hostname": "MacBook-Pro",
        "vendor": "Apple",
        "os_guess": "macOS",
        "dhcp_params": "1,3,6,15,119,121,108,252",
        "domains": [
            "api.twitter.com", "abs.twimg.com",
            "api.slack.com", "slack.com",
            "www.notion.so", "api.notion.com",
            "zoom.us", "api.zoom.us",
            "mail.google.com", "calendar.google.com", "drive.google.com",
            "www.figma.com", "api.figma.com",
            "www.spotify.com", "api.spotify.com",
        ],
        "sni_hosts": [
            "slack.com", "zoom.us", "api.notion.com", "mail.google.com", "api.spotify.com",
        ],
        "ja3_samples": [
            "bcd234e5f6789012345678901234abcd",
            "e7d705a3286e1ea8e910c2f49a1a4d4f",
        ],
        "mdns_services": [
            "_airplay._tcp.local",
            "_raop._tcp.local",
            "_companion-link._tcp.local",
        ],
    },
    {
        "mac": "b8:27:eb:11:22:33",
        "ip": "192.168.50.13",
        "hostname": "raspberrypi",
        "vendor": "Raspberry Pi Foundation",
        "os_guess": "Linux",
        "dhcp_params": "1,3,6,12,15,28,42,119",
        "domains": [
            "archive.raspberrypi.org",
            "downloads.raspberrypi.org",
            "api.github.com", "github.com",
            "pypi.org", "files.pythonhosted.org",
            "hub.docker.com", "registry-1.docker.io",
        ],
        "sni_hosts": [
            "api.github.com", "registry-1.docker.io", "pypi.org",
        ],
        "ja3_samples": [
            "9a8b7c6d5e4f32109876543210fedcb",
        ],
        "mdns_services": [
            "_ssh._tcp.local",
            "_device-info._tcp.local",
        ],
    },
    {
        "mac": "e4:5f:01:aa:bb:cc",
        "ip": "192.168.50.14",
        "hostname": "Galaxy-S21",
        "vendor": "Samsung",
        "os_guess": "Android",
        "dhcp_params": "1,3,6,28,51,58,59,43,114,119,120,121",
        "domains": [
            "android.googleapis.com", "play.google.com",
            "www.tiktok.com", "api.tiktok.com",
            "api.snapchat.com", "app.snapchat.com",
            "www.facebook.com", "graph.facebook.com",
            "api.spotify.com", "spclient.wg.spotify.com",
            "www.netflix.com", "api-global.netflix.com",
        ],
        "sni_hosts": [
            "play.google.com", "graph.facebook.com", "api.spotify.com",
            "api.tiktok.com", "www.netflix.com",
        ],
        "ja3_samples": [
            "112233445566778899aabbccddeeff00",
            "deadbeefcafebabe0123456789abcdef",
        ],
        "mdns_services": [
            "_googlecast._tcp.local",
            "_androidtvremote._tcp.local",
        ],
    },
]


def _db_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "wispy.db")


def _clear_all_data(conn):
    for table in (
        "devices",
        "dns_requests",
        "tls_sni",
        "ja3_fingerprints",
        "mdns_broadcasts",
        "flow_sessions",
        "plaintext_events",
    ):
        conn.execute(f"DELETE FROM {table}")
    conn.execute(
        "DELETE FROM sqlite_sequence WHERE name IN "
        "('dns_requests', 'tls_sni', 'ja3_fingerprints', 'mdns_broadcasts', 'flow_sessions', 'plaintext_events')"
    )


def generate_mock_data(num_queries_per_device=15):
    """Generate realistic mock data for dashboard testing."""
    init_db()

    print("[*] generating mock stuff (devices dns tls ja3 mdns flows etc)\n")

    now = datetime.utcnow()
    db_file = _db_path()
    conn = sqlite3.connect(db_file)

    for device in MOCK_DEVICES:
        first_seen = now - timedelta(minutes=random.randint(5, 60))
        upsert_device(
            mac=device["mac"],
            ip=device["ip"],
            hostname=device["hostname"],
            vendor=device["vendor"],
            os_guess=device["os_guess"],
            dhcp_params=device.get("dhcp_params"),
        )

        print(f"[+] {device['hostname']} ({device['mac']}) - {device['vendor']} / {device['os_guess']}")

        dom_list = device["domains"]
        sni_list = device["sni_hosts"]
        ja3_list = device["ja3_samples"]
        mdns_list = device["mdns_services"]

        for i in range(num_queries_per_device):
            domain = random.choice(dom_list)
            query_time = first_seen + timedelta(minutes=random.randint(0, 55))
            conn.execute(
                "INSERT INTO dns_requests (device_mac, domain, timestamp) VALUES (?, ?, ?)",
                (device["mac"], domain, query_time.isoformat()),
            )

        # less tls/ja3 than dns but enough for the ui
        for _ in range(max(3, num_queries_per_device // 3)):
            ts = first_seen + timedelta(minutes=random.randint(0, 55))
            sni = random.choice(sni_list)
            conn.execute(
                "INSERT INTO tls_sni (device_mac, sni, timestamp) VALUES (?, ?, ?)",
                (device["mac"], sni, ts.isoformat()),
            )
            ja3 = random.choice(ja3_list)
            conn.execute(
                "INSERT INTO ja3_fingerprints (device_mac, ja3_hash, timestamp) VALUES (?, ?, ?)",
                (device["mac"], ja3, ts.isoformat()),
            )

        for _ in range(max(2, num_queries_per_device // 5)):
            ts = first_seen + timedelta(minutes=random.randint(0, 55))
            svc = random.choice(mdns_list)
            conn.execute(
                "INSERT INTO mdns_broadcasts (device_mac, service_name, timestamp) VALUES (?, ?, ?)",
                (device["mac"], svc, ts.isoformat()),
            )

        # mock flow sessions
        for _ in range(5):
            ts = first_seen + timedelta(minutes=random.randint(0, 55))
            proto = "TCP"
            dst_port = random.choice([443, 80, 22, 8080])
            svc_label = "HTTPS" if dst_port == 443 else ("HTTP" if dst_port == 80 else ("SSH" if dst_port == 22 else "HTTP-ALT"))
            
            if dst_port == 443:
                dst_host = random.choice(sni_list)
                host_source = "sni"
            elif dst_port == 80:
                dst_host = random.choice(dom_list)
                host_source = "dns"
            else:
                dst_host = "unknown"
                host_source = "unknown"
                
            pkt_cnt = random.randint(10, 500)
            byte_cnt = pkt_cnt * random.randint(64, 1400)
            
            conn.execute("""
                INSERT INTO flow_sessions (device_mac, proto, src_ip, dst_ip, dst_port, dst_host, host_source, first_seen, last_seen, packet_count, byte_count, service_label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (device["mac"], proto, device["ip"], f"142.250.{random.randint(1,254)}.{random.randint(1,254)}", dst_port, dst_host, host_source, ts.isoformat(), (ts + timedelta(seconds=random.randint(5, 300))).isoformat(), pkt_cnt, byte_cnt, svc_label))

        # plaintext samples for a couple devices
        if device["mac"] == "a4:83:e7:12:34:56":  # johns iphone
            ts = first_seen + timedelta(minutes=10)
            conn.execute("""
                INSERT INTO plaintext_events (device_mac, proto, host_or_server, method_or_command, body, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (device["mac"], "http", "detectportal.firefox.com", "GET", "GET /success.txt HTTP/1.1\r\nHost: detectportal.firefox.com\r\nUser-Agent: Mozilla/5.0\r\nAccept: */*\r\nConnection: close\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 8\r\n\r\nsuccess\n", ts.isoformat()))
            
        elif device["mac"] == "dc:a6:32:ab:cd:ef":  # dell desktop
            ts = first_seen + timedelta(minutes=15)
            conn.execute("""
                INSERT INTO plaintext_events (device_mac, proto, host_or_server, method_or_command, body, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (device["mac"], "smtp", "mail.example.com", "EHLO", "220 mail.example.com ESMTP Postfix\r\nEHLO DESKTOP-8H3KL2\r\n250-mail.example.com\r\n250-PIPELINING\r\n250-SIZE 10240000\r\n250-ETRN\r\n250-STARTTLS\r\n250-ENHANCEDSTATUSCODES\r\n250-8BITMIME\r\n250-DSN\r\n250-SMTPUTF8\r\n250 CHUNKING\r\n", ts.isoformat()))

        print(f"    done - dns/tls/ja3/mdns/flows/plaintext for this device")
        conn.commit()

    conn.close()

    print(f"\n[+] mock data done")
    print(f"[+] devices: {len(MOCK_DEVICES)}")
    print(f"[+] dns rows (approx): {len(MOCK_DEVICES) * num_queries_per_device}")
    print(f"\n[*] run dashboard: python web/app.py")


def add_more_queries(num_additional=10):
    """Add more DNS queries to existing devices for testing real-time updates."""
    print(f"[*] adding {num_additional} extra dns per device...\n")

    for device in MOCK_DEVICES:
        for _ in range(num_additional):
            domain = random.choice(device["domains"])
            insert_dns(device["mac"], domain)
        print(f"[+] +{num_additional} dns for {device['hostname']}")

    print(f"\n[+] done, refresh the dashboard to see new rows")


if __name__ == "__main__":
    if "--reset" in sys.argv:
        print("[!] wiping db...")
        init_db()
        with sqlite3.connect(_db_path()) as conn:
            _clear_all_data(conn)
            conn.commit()
        print("[+] db cleared\n")

    if "--more" in sys.argv:
        add_more_queries(num_additional=20)
    else:
        q_per_dev = 25 if "--many" in sys.argv else 15
        generate_mock_data(num_queries_per_device=q_per_dev)
