import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scapy.all import sniff, DNSQR, DNS, Ether, IP, DHCP, BOOTP
from dotenv import load_dotenv
from analysis.storage import init_db, upsert_device, insert_dns
from core.fingerprint import fingerprint

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

INTERFACE = os.getenv("WIFI_INTERFACE", "wlan0")


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
    for opt in packet[DHCP].options:
        if isinstance(opt, tuple) and opt[0] == 'hostname':
            raw = opt[1]
            hostname = raw.decode(errors='ignore') if isinstance(raw, bytes) else raw
            break

    if not hostname:
        return

    ip = packet[BOOTP].ciaddr or None
    if ip == '0.0.0.0':
        ip = None

    upsert_device(mac, ip=ip, hostname=hostname)
    print(f"[DHCP] {mac} → hostname: {hostname}")


def process_packet(packet):
    if packet.haslayer(DHCP):
        _handle_dhcp(packet)
    else:
        _handle_dns(packet)


def start():
    init_db()
    print(f"[*] Sniffing on interface: {INTERFACE}")
    print("[*] Listening for DNS queries... Press Ctrl+C to stop.\n")
    sniff(
        iface=INTERFACE,
        filter="udp port 53 or udp port 67 or udp port 68",
        prn=process_packet,
        store=False,
    )


if __name__ == '__main__':
    start()
