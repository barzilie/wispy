"""
In-memory DNS-to-IP correlation cache for mapping flow destination IPs to hostnames.
"""
import time

# Cache of (device_mac, ip_addr) -> (domain, timestamp)
_dns_ip_cache = {}
DNS_CACHE_TTL_SEC = 900  # 15 minutes TTL


def add_dns_mapping(device_mac, ip, domain):
    """Caches a mapping from device_mac and IP to resolved domain."""
    if not device_mac or not ip or not domain:
        return
    _dns_ip_cache[(device_mac, ip)] = (domain, time.time())


def resolve_ip_to_host(device_mac, ip):
    """Resolves a destination IP back to a domain using cached DNS replies.
    
    Returns (domain, host_source) or (None, 'unknown').
    """
    if not device_mac or not ip:
        return None, "unknown"

    key = (device_mac, ip)
    if key in _dns_ip_cache:
        domain, timestamp = _dns_ip_cache[key]
        if time.time() - timestamp <= DNS_CACHE_TTL_SEC:
            return domain, "dns"
        else:
            # Expired
            del _dns_ip_cache[key]

    return None, "unknown"
