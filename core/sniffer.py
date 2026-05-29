import os
import sys
import hashlib
import socket
import time
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scapy.all import sniff, DNSQR, DNSRR, DNS, Ether, IP, DHCP, BOOTP, UDP, TCP, Raw
from dotenv import load_dotenv
from analysis.storage import (
    init_db,
    upsert_device,
    insert_dns,
    insert_mdns,
    insert_tls_sni,
    insert_ja3,
    upsert_flow_session,
    insert_plaintext,
)
from analysis.dns_filters import is_ad_tracking_domain
from analysis.correlation import add_dns_mapping, resolve_ip_to_host
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
HTTP_SMTP_DEDUP_WINDOW_SEC = 60

_last_mdns_seen = {}
_last_sni_seen = {}
_last_ja3_seen = {}
_last_plaintext_seen = {}

# Flow session tracking
_active_flows = {}
_last_flow_flush = time.time()
FLOW_FLUSH_INTERVAL_SEC = 5


def _should_emit(cache, key, window_sec):
    now = time.time()
    last_seen = cache.get(key)
    if last_seen is not None and (now - last_seen) < window_sec:
        return False
    cache[key] = now
    return True


def _dns_rr_to_ip(rr_type, rr_data):
    """Normalize DNS A/AAAA rdata to a printable IP string."""
    if rr_data is None:
        return None
    if rr_type == 1:
        if isinstance(rr_data, bytes):
            if len(rr_data) == 4:
                return socket.inet_ntoa(rr_data)
            try:
                return rr_data.decode(errors="ignore")
            except Exception:
                return None
        return str(rr_data)
    if rr_type == 28:
        if isinstance(rr_data, bytes) and len(rr_data) == 16:
            try:
                return socket.inet_ntop(socket.AF_INET6, rr_data)
            except (OSError, ValueError):
                return None
        return str(rr_data)
    return None


def _normalize_name(raw_name):
    if raw_name is None:
        return None
    if isinstance(raw_name, bytes):
        return raw_name.decode(errors="ignore").rstrip(".")
    return str(raw_name).rstrip(".")


def _handle_dns(packet):
    if not packet.haslayer(DNS):
        return
    dns = packet[DNS]

    if dns.qr == 0:  # Query
        if not packet.haslayer(DNSQR):
            return
        mac = packet[Ether].src if packet.haslayer(Ether) else "00:00:00:00:00:00"
        ip  = packet[IP].src if packet.haslayer(IP) else None
        ttl = packet[IP].ttl if packet.haslayer(IP) else None
        domain = packet[DNSQR].qname.decode(errors='ignore').rstrip('.')

        if not domain or domain.endswith('.local'):
            return
        if is_ad_tracking_domain(domain):
            return

        fp = fingerprint(mac, ttl)
        upsert_device(mac, ip=ip, vendor=fp["vendor"], os_guess=fp["os_guess"])
        insert_dns(mac, domain)
        print(f"[DNS]  {mac} → {domain}")
        
    elif dns.qr == 1:  # Response
        mac = packet[Ether].dst if packet.haslayer(Ether) else None
        if not mac:
            return
        # Parse answers
        i = 1
        while True:
            rr = packet.getlayer(DNSRR, i)
            if not rr:
                break
            rr_type = rr.type
            rr_name = _normalize_name(rr.rrname)
            rr_data = rr.rdata
            if rr_type in (1, 28) and rr_name and rr_data:
                ip_str = _dns_rr_to_ip(rr_type, rr_data)
                if ip_str:
                    add_dns_mapping(mac, ip_str, rr_name)
            i += 1


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
        src_ip = packet[IP].src if packet.haslayer(IP) else None
        dst_ip = packet[IP].dst if packet.haslayer(IP) else None

        if sni:
            if _should_emit(_last_sni_seen, (mac, sni), TLS_SNI_DEDUP_WINDOW_SEC):
                insert_tls_sni(mac, sni)
                print(f"[TLS]  {mac} → SNI: {sni}")
            
            # Tie SNI to active TCP/443 flow
            if src_ip and dst_ip:
                flow_key = (mac, "TCP", src_ip, dst_ip, 443)
                if flow_key in _active_flows:
                    _active_flows[flow_key]['dst_host'] = sni
                    _active_flows[flow_key]['host_source'] = 'sni'

        ja3_hash = _ja3_from_client_hello(msg)
        if ja3_hash:
            if _should_emit(_last_ja3_seen, (mac, ja3_hash), JA3_DEDUP_WINDOW_SEC):
                insert_ja3(mac, ja3_hash)
                print(f"[JA3]  {mac} → {ja3_hash}")


def _is_private_ip(ip):
    if not ip:
        return False
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        p0 = int(parts[0])
        p1 = int(parts[1])
        if p0 == 10:
            return True
        if p0 == 172 and 16 <= p1 <= 31:
            return True
        if p0 == 192 and p1 == 168:
            return True
        if p0 == 127:
            return True
    except ValueError:
        return False
    return False


def _get_service_label(port):
    labels = {
        80: "HTTP",
        443: "HTTPS",
        25: "SMTP",
        53: "DNS",
        5353: "mDNS",
        22: "SSH",
        21: "FTP",
        123: "NTP",
        143: "IMAP",
        110: "POP3",
        1883: "MQTT",
        8080: "HTTP-ALT"
    }
    return labels.get(port, f"TCP/UDP-{port}" if port else "UNKNOWN")


def _track_packet_flow(packet):
    global _active_flows
    if not packet.haslayer(IP):
        return
    
    ip_layer = packet[IP]
    src_ip = ip_layer.src
    dst_ip = ip_layer.dst
    
    src_private = _is_private_ip(src_ip)
    dst_private = _is_private_ip(dst_ip)
    
    if src_private and not dst_private:
        client_mac = packet[Ether].src if packet.haslayer(Ether) else None
        client_ip = src_ip
        server_ip = dst_ip
        server_port = packet[TCP].dport if packet.haslayer(TCP) else (packet[UDP].dport if packet.haslayer(UDP) else 0)
        proto = "TCP" if packet.haslayer(TCP) else ("UDP" if packet.haslayer(UDP) else "IP")
    elif dst_private and not src_private:
        client_mac = packet[Ether].dst if packet.haslayer(Ether) else None
        client_ip = dst_ip
        server_ip = src_ip
        server_port = packet[TCP].sport if packet.haslayer(TCP) else (packet[UDP].sport if packet.haslayer(UDP) else 0)
        proto = "TCP" if packet.haslayer(TCP) else ("UDP" if packet.haslayer(UDP) else "IP")
    else:
        client_mac = packet[Ether].src if packet.haslayer(Ether) else None
        client_ip = src_ip
        server_ip = dst_ip
        server_port = packet[TCP].dport if packet.haslayer(TCP) else (packet[UDP].dport if packet.haslayer(UDP) else 0)
        proto = "TCP" if packet.haslayer(TCP) else ("UDP" if packet.haslayer(UDP) else "IP")
        
    if not client_mac:
        return
        
    flow_key = (client_mac, proto, client_ip, server_ip, server_port)
    now_epoch = time.time()
    now_iso = datetime.utcnow().isoformat()
    
    if flow_key not in _active_flows:
        dst_host, host_source = resolve_ip_to_host(client_mac, server_ip)
        service_label = _get_service_label(server_port)
        
        _active_flows[flow_key] = {
            'client_mac': client_mac,
            'proto': proto,
            'client_ip': client_ip,
            'server_ip': server_ip,
            'server_port': server_port,
            'dst_host': dst_host or "unknown",
            'host_source': host_source,
            'service_label': service_label,
            'first_seen': now_iso,
            'last_seen': now_iso,
            'last_seen_epoch': now_epoch,
            'new_packets': 0,
            'new_bytes': 0
        }
        
    flow = _active_flows[flow_key]
    flow['last_seen'] = now_iso
    flow['last_seen_epoch'] = now_epoch
    flow['new_packets'] += 1
    flow['new_bytes'] += len(packet)
    
    if flow['dst_host'] == "unknown" or flow['host_source'] == "unknown":
        dst_host, host_source = resolve_ip_to_host(client_mac, server_ip)
        if dst_host:
            flow['dst_host'] = dst_host
            flow['host_source'] = host_source


def _flush_flows_to_db():
    global _active_flows, _last_flow_flush
    now_epoch = time.time()
    keys_to_remove = []
    
    for key, flow in list(_active_flows.items()):
        if flow['new_packets'] > 0:
            upsert_flow_session(
                device_mac=flow['client_mac'],
                proto=flow['proto'],
                src_ip=flow['client_ip'],
                dst_ip=flow['server_ip'],
                dst_port=flow['server_port'],
                dst_host=flow['dst_host'],
                host_source=flow['host_source'],
                packet_count=flow['new_packets'],
                byte_count=flow['new_bytes'],
                first_seen=flow['first_seen'],
                last_seen=flow['last_seen'],
                service_label=flow['service_label']
            )
            flow['new_packets'] = 0
            flow['new_bytes'] = 0
            
        if now_epoch - flow['last_seen_epoch'] > 60:
            keys_to_remove.append(key)
            
    for k in keys_to_remove:
        if k in _active_flows:
            del _active_flows[k]
            
    _last_flow_flush = now_epoch


def _parse_http_payload(payload):
    try:
        text = payload.decode(errors='ignore')
        lines = text.split('\r\n')
        if not lines:
            return None
        req_line = lines[0]
        parts = req_line.split(' ')
        if len(parts) < 3 or not parts[2].startswith('HTTP/'):
            return None
        
        method = parts[0]
        
        host = "unknown"
        for line in lines[1:]:
            if line.lower().startswith('host:'):
                host = line[5:].strip()
                break
        return {
            'host': host,
            'method': method,
            'summary': req_line
        }
    except Exception:
        return None


def _parse_smtp_payload(payload):
    try:
        text = payload.decode(errors='ignore')
        lines = text.split('\r\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('220 '):
                parts = line.split(' ')
                server = parts[1] if len(parts) > 1 else "unknown"
                return {
                    'server': server,
                    'command': 'GREETING',
                    'summary': line[:100]
                }
            for cmd in ('EHLO', 'HELO', 'MAIL FROM', 'RCPT TO', 'DATA', 'STARTTLS'):
                if line.upper().startswith(cmd):
                    return {
                        'server': 'unknown',
                        'command': cmd,
                        'summary': line[:100]
                    }
    except Exception:
        return None


def _handle_plaintext(packet):
    if not (packet.haslayer(TCP) and packet.haslayer(Raw)):
        return
    
    tcp = packet[TCP]
    sport = tcp.sport
    dport = tcp.dport
    
    if sport != 80 and dport != 80 and sport != 25 and dport != 25:
        return
        
    payload = bytes(packet[Raw])
    # Skip if it looks like TLS/SSL handshake
    if len(payload) > 5 and payload[0] == 0x16 and payload[1] == 0x03:
        return
        
    src_ip = packet[IP].src if packet.haslayer(IP) else None
    dst_ip = packet[IP].dst if packet.haslayer(IP) else None
    src_mac = packet[Ether].src if packet.haslayer(Ether) else None
    dst_mac = packet[Ether].dst if packet.haslayer(Ether) else None
    
    # Identify client MAC using private IP check
    if _is_private_ip(src_ip):
        client_mac = src_mac
    elif _is_private_ip(dst_ip):
        client_mac = dst_mac
    else:
        client_mac = src_mac
        
    if not client_mac:
        return
        
    if sport == 80 or dport == 80:
        res = _parse_http_payload(payload)
        if res:
            key = (client_mac, "http", res['host'], res['method'], res['summary'])
            if _should_emit(_last_plaintext_seen, key, HTTP_SMTP_DEDUP_WINDOW_SEC):
                body_text = payload.decode(errors='ignore')
                insert_plaintext(client_mac, "http", res['host'], res['method'], body_text)
                print(f"[HTTP] {client_mac} → {res['host']} ({res['method']})")
                
    elif sport == 25 or dport == 25:
        res = _parse_smtp_payload(payload)
        if res:
            key = (client_mac, "smtp", res['server'], res['command'], res['summary'])
            if _should_emit(_last_plaintext_seen, key, HTTP_SMTP_DEDUP_WINDOW_SEC):
                body_text = payload.decode(errors='ignore')
                insert_plaintext(client_mac, "smtp", res['server'], res['command'], body_text)
                print(f"[SMTP] {client_mac} → {res['command']}")


def process_packet(packet):
    if packet.haslayer(DHCP):
        _handle_dhcp(packet)
    if packet.haslayer(DNS):
        _handle_mdns(packet)
        _handle_dns(packet)
    if packet.haslayer(TCP):
        _handle_tls(packet)
        _handle_plaintext(packet)
        
    # Track IP flow sessions
    if packet.haslayer(IP):
        _track_packet_flow(packet)
        
    # Flush flow updates periodically
    if time.time() - _last_flow_flush > FLOW_FLUSH_INTERVAL_SEC:
        _flush_flows_to_db()


def start():
    init_db()
    print(f"[*] Sniffing on interface: {INTERFACE}")
    print("[*] Listening for DNS, mDNS, DHCP, TLS, HTTP, SMTP... Press Ctrl+C to stop.\n")
    sniff(
        iface=INTERFACE,
        filter="udp port 53 or udp port 5353 or udp port 67 or udp port 68 or tcp port 443 or tcp port 80 or tcp port 25",
        prn=process_packet,
        store=False,
    )


if __name__ == '__main__':
    start()

