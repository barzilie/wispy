import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# fingerprint.py
from mac_vendor_lookup import MacLookup
from scapy.all import conf

_TTL_MAP = [
    (range(60, 66),  "Linux / Android / Apple"), 
    (range(124, 130), "Windows"),
    (range(253, 256), "Network Device"),
]

CONFIDENCE_MAP = {'http_ua': 100, 'dhcp_55': 80, 'ttl': 40}

def lookup_vendor(mac: str) -> str | None:
    try:
        vendor = MacLookup().lookup(mac)
        if vendor: return vendor
    except Exception: pass
    try:
        result = conf.manufdb._get_manuf(mac)
        return result if result and result.lower() != mac.lower() else None
    except Exception: return None

def guess_os(ttl: int) -> str | None:
    for r, name in _TTL_MAP:
        if ttl in r: return name
    return None

def guess_os_from_opt55(opt55_str: str) -> str | None:
    if not opt55_str: return None
    if opt55_str.startswith("1,3,6,15,26,28,51"): return "Android"
    if opt55_str.startswith("1,3,6,15,119,252"): return "Apple (iOS/macOS)"
    if "31,33,43,44,46,47" in opt55_str or opt55_str.startswith("1,3,6,15,31"): return "Windows"
    return None

def guess_os_from_http(user_agent: str) -> str | None:
    if not user_agent: return None
    ua = user_agent.lower()
    if any(x in ua for x in ['iphone', 'ipad', 'mac os x']): return "Apple (iOS/macOS)"
    if 'android' in ua: return "Android"
    if 'windows nt' in ua: return "Windows"
    if 'linux' in ua: return "Linux"
    return None

class OSResolver:
    @staticmethod
    def evaluate(signal_type: str, signal_value, current_confidence: int = 0):
        if signal_type not in CONFIDENCE_MAP:
            return None, current_confidence
        new_conf = CONFIDENCE_MAP[signal_type]
        if new_conf < current_confidence:
            return None, current_confidence
        
        # Dispatch to the correct guesser
        guessers = {
            'http_ua': guess_os_from_http,
            'dhcp_55': guess_os_from_opt55,
            'ttl': guess_os
        }
        new_os = guessers[signal_type](signal_value)
        return (new_os, new_conf) if new_os else (None, current_confidence)


def fingerprint(mac: str, ttl: int | None = None) -> dict:
    """Returns vendor and os_guess for a device. Either field may be None."""
    return {
        "vendor": lookup_vendor(mac),
        "os_guess": guess_os(ttl) if ttl is not None else None,
    }
