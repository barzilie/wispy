import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scapy.all import conf

# ttl on our ap is basically 1 hop from client so these ranges work ok
_TTL_MAP = [
    (range(60, 66),  "Linux / Android"),
    (range(124, 130), "Windows"),
    (range(253, 256), "Network Device"),
]


def lookup_vendor(mac: str) -> str | None:
    try:
        result = conf.manufdb._get_manuf(mac)
        return result if result else None
    except Exception:
        return None


def guess_os(ttl: int) -> str | None:
    for r, name in _TTL_MAP:
        if ttl in r:
            return name
    return None


def fingerprint(mac: str, ttl: int | None = None) -> dict:
    """Returns vendor and os_guess for a device. Either field may be None."""
    return {
        "vendor": lookup_vendor(mac),
        "os_guess": guess_os(ttl) if ttl is not None else None,
    }
