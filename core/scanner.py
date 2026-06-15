import subprocess
import re
import time
import threading


def enable_monitor_mode(interface="wlan0"):
    """Switches the interface to monitor mode. Returns the monitor interface name."""
    # kill networkmanager etc so airmon works
    subprocess.run(["airmon-ng", "check", "kill"], capture_output=True)
    subprocess.run(["airmon-ng", "start", interface], capture_output=True, text=True)
    time.sleep(1)

    # iw dev usually tells us the mon iface name
    mon_if = _find_monitor_interface()
    if mon_if:
        return mon_if

    # fallback guesses
    for guess in [interface + "mon", interface]:
        r = subprocess.run(["ip", "link", "show", guess], capture_output=True)
        if r.returncode == 0:
            return guess

    return interface


def disable_monitor_mode(mon_interface="wlan0mon"):
    subprocess.run(["airmon-ng", "stop", mon_interface], capture_output=True)


def _find_monitor_interface():
    """Parse 'iw dev' output to find any interface currently in monitor mode."""
    result = subprocess.run(["iw", "dev"], capture_output=True, text=True)
    current_iface = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Interface"):
            current_iface = line.split()[1]
        elif line == "type monitor" and current_iface:
            return current_iface
    return None


def _channel_hopper(interface, stop_event):
    """Cycles through 2.4 GHz channels while scanning."""
    channels = [1, 6, 11, 2, 7, 12, 3, 8, 13, 4, 9, 5, 10]
    while not stop_event.is_set():
        for ch in channels:
            if stop_event.is_set():
                return
            subprocess.run(
                ["iw", "dev", interface, "set", "channel", str(ch)],
                capture_output=True,
            )
            time.sleep(0.4)


def scan_networks(mon_interface="wlan0", duration=15):
    """
    Sniffs 802.11 beacon frames with Scapy and returns a list of network dicts.
    Runs a channel-hopper thread to cover all 2.4 GHz channels.
    """
    from scapy.all import sniff, Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt

    found_nets = {}  # bssid -> net dict, skip dupes

    def handle_packet(pkt):
        if not (pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp)):
            return

        bssid = pkt[Dot11].addr2
        if not bssid or bssid in found_nets:
            return

        try:
            ssid = pkt[Dot11Elt].info.decode("utf-8", errors="ignore").strip()
        except Exception:
            return
        if not ssid:
            return

        # channel from DS param element id 3
        chan = 6
        elt = pkt[Dot11Elt]
        while elt and hasattr(elt, "ID"):
            if elt.ID == 3 and elt.len == 1:
                chan = elt.info[0] if isinstance(elt.info, (bytes, bytearray)) else elt.info
                break
            elt = elt.payload

        # privacy bit = wpa usually
        if pkt.haslayer(Dot11Beacon):
            cap = pkt[Dot11Beacon].cap
        else:
            cap = pkt[Dot11ProbeResp].cap
        enc_type = "WPA" if cap.privacy else "Open"

        found_nets[bssid] = {
            "ssid": ssid,
            "bssid": bssid,
            "channel": int(chan),
            "encryption": enc_type,
        }

    stop_event = threading.Event()
    hopper = threading.Thread(
        target=_channel_hopper, args=(mon_interface, stop_event), daemon=True
    )
    hopper.start()

    print(f"[*] sniffing beacons on {mon_interface} for {duration}s...")
    sniff(iface=mon_interface, prn=handle_packet, timeout=duration, store=False)

    stop_event.set()
    hopper.join(timeout=2)

    # one entry per ssid
    seen = set()
    out = []
    for net in found_nets.values():
        if net["ssid"] not in seen:
            seen.add(net["ssid"])
            out.append(net)

    return out


def prompt_user_selection(networks):
    print("\nfound networks:\n")
    for i, net in enumerate(networks):
        enc = net.get("encryption", "?")
        chan = net.get("channel", "?")
        print(f"  [{i+1}] SSID: {net['ssid']:<30} ch: {chan:<4} enc: {enc}")

    print()
    while True:
        try:
            pick = int(input("pick network number to mimic: ")) - 1
            if 0 <= pick < len(networks):
                return networks[pick]
        except ValueError:
            pass
        print("bad choice, try again")
