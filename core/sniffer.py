import os
import sys
import hashlib
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scapy.all import sniff, DNSQR, DNS, Ether, IP, DHCP, BOOTP, UDP, TCP
from dotenv import load_dotenv
from analysis.storage import (
    init_db,
    upsert_device,
    insert_dns,
    insert_mdns,
    insert_tls_sni,
    insert_ja3,
)
from core.fingerprint import fingerprint
try:
    from scapy.layers.tls.all import TLS, TLSClientHello  # type: ignore
except Exception:
    TLS = None
    TLSClientHello = None

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

INTERFACE = os.getenv("WIFI_INTERFACE", "wlan0")
MDNS_DEDUP_WINDOW_SEC = int(os.getenv("MDNS_DEDUP_WINDOW_SEC", "120"))
TLS_SNI_DEDUP_WINDOW_SEC = int(os.getenv("TLS_SNI_DEDUP_WINDOW_SEC", "300"))
JA3_DEDUP_WINDOW_SEC = int(os.getenv("JA3_DEDUP_WINDOW_SEC", "300"))

_last_mdns_seen = {}
_last_sni_seen = {}
_last_ja3_seen = {}


def _should_emit(cache, key, window_sec):
    now = time.time()
    last_seen = cache.get(key)
    if last_seen is not None and (now - last_seen) < window_sec:
        return False
    cache[key] = now
    return True


def _normalize_name(raw_name):
    if raw_name is None:
        return None
    if isinstance(raw_name, bytes):
        return raw_name.decode(errors="ignore").rstrip(".")
    return str(raw_name).rstrip(".")


def _handle_dns(packet):
    if not (packet.haslayer(DNS) and packet.haslayer(DNSQR)):
        return
    if packet[DNS].qr != 0:
        return

    mac = packet[Ether].src if packet.haslayer(Ether) else "00:00:00:00:00:00"
    ip  = packet[IP].src if packet.haslayer(IP) else None
    ttl = packet[IP].ttl if packet.haslayer(IP) else None
    domain = packet[DNSQR].qname.decode(errors='ignore').rstrip('.')

    if not domain or domain.endswith('.local'):
        return

    fp = fingerprint(mac, ttl)
    upsert_device(mac, ip=ip, vendor=fp["vendor"], os_guess=fp["os_guess"])
    insert_dns(mac, domain)
    print(f"[DNS]  {mac} → {domain}")


def _handle_dhcp(packet):
    if not (packet.haslayer(DHCP) and packet.haslayer(BOOTP) and packet.haslayer(Ether)):
        return

    mac = packet[Ether].src
    hostname = None
    dhcp_params = None
    for opt in packet[DHCP].options:
        if isinstance(opt, tuple) and opt[0] == 'hostname':
            raw = opt[1]
            hostname = raw.decode(errors='ignore') if isinstance(raw, bytes) else raw
        if isinstance(opt, tuple) and opt[0] == 'param_req_list':
            raw = opt[1]
            if isinstance(raw, bytes):
                dhcp_params = ",".join(str(v) for v in raw)
            elif isinstance(raw, (list, tuple)):
                dhcp_params = ",".join(str(v) for v in raw)
            else:
                dhcp_params = str(raw)

    if not hostname and not dhcp_params:
        return

    ip = packet[BOOTP].ciaddr or None
    if ip == '0.0.0.0':
        ip = None

    upsert_device(mac, ip=ip, hostname=hostname, dhcp_params=dhcp_params)
    print(f"[DHCP] {mac} → hostname: {hostname}, option55: {dhcp_params}")


def _extract_mdns_name(packet):
    dns = packet[DNS]
    # Queries
    if dns.qdcount and hasattr(dns, "qd") and dns.qd is not None:
        qd = dns.qd
        while isinstance(qd, DNSQR):
            name = _normalize_name(getattr(qd, "qname", None))
            if name:
                return name
            qd = getattr(qd, "payload", None)
            if qd is None:
                break

    # Resource records (responses/announcements)
    rr = getattr(dns, "an", None)
    if rr is not None:
        name = _normalize_name(getattr(rr, "rrname", None))
        if name:
            return name
    return None


def _handle_mdns(packet):
    if not (packet.haslayer(UDP) and packet.haslayer(DNS) and packet.haslayer(Ether)):
        return
    udp = packet[UDP]
    if udp.sport != 5353 and udp.dport != 5353:
        return

    name = _extract_mdns_name(packet)
    if not name:
        return
    # Keep local service broadcasts and reduce mDNS noise.
    if not name.endswith(".local"):
        return
    if "_" not in name:
        return

    mac = packet[Ether].src
    if not _should_emit(_last_mdns_seen, (mac, name), MDNS_DEDUP_WINDOW_SEC):
        return
    insert_mdns(mac, name)
    print(f"[mDNS] {mac} → {name}")


def _ja3_from_client_hello(client_hello):
    version = str(getattr(client_hello, "version", ""))
    ciphers = "-".join(str(v) for v in (getattr(client_hello, "ciphers", []) or []))
    exts = getattr(client_hello, "ext", []) or []

    ext_types = []
    curves = []
    ec_point_formats = []
    for ext in exts:
        ext_type = getattr(ext, "type", None)
        if ext_type is not None:
            ext_types.append(str(ext_type))
        if ext_type == 10:
            groups = getattr(ext, "groups", []) or []
            curves.extend(str(v) for v in groups)
        if ext_type == 11:
            fmts = getattr(ext, "ecpl", []) or []
            ec_point_formats.extend(str(v) for v in fmts)

    ja3_string = ",".join([
        version,
        ciphers,
        "-".join(ext_types),
        "-".join(curves),
        "-".join(ec_point_formats),
    ])
    if ja3_string == ",,,,":
        return None
    return hashlib.md5(ja3_string.encode("utf-8")).hexdigest()


def _extract_sni(client_hello):
    exts = getattr(client_hello, "ext", []) or []
    for ext in exts:
        if getattr(ext, "type", None) != 0:
            continue
        server_names = getattr(ext, "servernames", []) or []
        for server_name in server_names:
            name = _normalize_name(getattr(server_name, "servername", None))
            if name:
                return name
    return None


def _handle_tls(packet):
    if TLS is None or TLSClientHello is None:
        return
    if not (packet.haslayer(TCP) and packet.haslayer(Ether) and packet.haslayer(TLS)):
        return

    tcp = packet[TCP]
    if tcp.sport != 443 and tcp.dport != 443:
        return

    tls = packet[TLS]
    messages = getattr(tls, "msg", []) or []
    if not isinstance(messages, list):
        messages = [messages]

    for msg in messages:
        if not isinstance(msg, TLSClientHello):
            continue
        mac = packet[Ether].src
        sni = _extract_sni(msg)
        if sni:
            if _should_emit(_last_sni_seen, (mac, sni), TLS_SNI_DEDUP_WINDOW_SEC):
                insert_tls_sni(mac, sni)
                print(f"[TLS]  {mac} → SNI: {sni}")

        ja3_hash = _ja3_from_client_hello(msg)
        if ja3_hash:
            if _should_emit(_last_ja3_seen, (mac, ja3_hash), JA3_DEDUP_WINDOW_SEC):
                insert_ja3(mac, ja3_hash)
                print(f"[JA3]  {mac} → {ja3_hash}")


def process_packet(packet):
    if packet.haslayer(DHCP):
        _handle_dhcp(packet)
    if packet.haslayer(DNS):
        _handle_mdns(packet)
        _handle_dns(packet)
    if packet.haslayer(TCP):
        _handle_tls(packet)


def start():
    init_db()
    print(f"[*] Sniffing on interface: {INTERFACE}")
    print("[*] Listening for DNS, mDNS, DHCP, TLS metadata... Press Ctrl+C to stop.\n")
    sniff(
        iface=INTERFACE,
        filter="udp port 53 or udp port 5353 or udp port 67 or udp port 68 or tcp port 443",
        prn=process_packet,
        store=False,
    )


if __name__ == '__main__':
    start()
