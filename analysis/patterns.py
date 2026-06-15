"""
Heuristic analysis of device usage patterns based on flow sessions and DNS queries.
"""
import os
import time

from analysis.storage import get_flow_sessions, get_dns_requests, get_plaintext_events

PATTERN_CACHE_TTL_SEC = int(os.getenv("WISPY_PATTERN_CACHE_TTL_SEC", "15"))
PATTERN_POLL_QUERY_LIMIT = int(os.getenv("WISPY_PATTERN_POLL_LIMIT", "500"))
PATTERN_AGENT_QUERY_LIMIT = int(os.getenv("WISPY_PATTERN_AGENT_LIMIT", "2000"))

_pattern_cache = {}


def clear_pattern_cache():
    """Clears the in-memory pattern cache (e.g. after DB reset)."""
    _pattern_cache.clear()


def analyze_device_patterns(device_mac, *, query_limit=None, use_cache=True):
    """Analyzes flows, DNS, and plaintext for a device; optional TTL cache."""
    if query_limit is None:
        query_limit = PATTERN_POLL_QUERY_LIMIT

    if use_cache:
        hit = _pattern_cache.get(device_mac)
        if hit:
            ts, cached_out = hit
            if time.time() - ts <= PATTERN_CACHE_TTL_SEC:
                return cached_out

    flows = get_flow_sessions(limit=query_limit, device_mac=device_mac)
    dns = get_dns_requests(limit=query_limit, device_mac=device_mac)
    plaintext = get_plaintext_events(limit=query_limit, device_mac=device_mac)

    total_flows = len(flows)
    total_packets = sum(f.get("packet_count", 0) for f in flows)
    total_bytes = sum(f.get("byte_count", 0) for f in flows)

    hosts_seen = set()
    for f in flows:
        if f.get("dst_host") and f["dst_host"] != "unknown":
            hosts_seen.add(f["dst_host"].lower())
    for d in dns:
        if d.get("domain"):
            hosts_seen.add(d["domain"].lower())

    found_tags = []

    has_plaintext = len(plaintext) > 0
    if not has_plaintext:
        for f in flows:
            if f.get("dst_port") in (80, 25):
                has_plaintext = True
                break

    if has_plaintext:
        found_tags.append({
            "tag": "PLAINTEXT_LEAKS",
            "name": "Unencrypted Communication",
            "desc": "Plaintext HTTP or SMTP traffic observed. Content can be fully intercepted.",
            "severity": "high",
        })

    social_domains = {"instagram", "facebook", "twitter", "x.com", "tiktok", "snapchat", "whatsapp", "reddit"}
    social_hits = [h for h in hosts_seen if any(s in h for s in social_domains)]
    if social_hits:
        found_tags.append({
            "tag": "SOCIAL_MEDIA",
            "name": "Social Media Activity",
            "desc": f"Observed communication with social networks: {', '.join(set(social_hits[:3]))}.",
            "severity": "info",
        })

    work_domains = {"slack", "zoom", "microsoft", "office", "notion", "figma", "github", "stackoverflow", "teams"}
    work_hits = [h for h in hosts_seen if any(w in h for w in work_domains)]
    if work_hits:
        found_tags.append({
            "tag": "WORK_COLLAB",
            "name": "Work & Collaboration",
            "desc": f"Active communication with work/development suites: {', '.join(set(work_hits[:3]))}.",
            "severity": "info",
        })

    stream_domains = {"youtube", "netflix", "spotify", "twitch", "ytimg"}
    stream_hits = [h for h in hosts_seen if any(st in h for st in stream_domains)]
    if stream_hits or total_bytes > 5 * 1024 * 1024:
        found_tags.append({
            "tag": "MEDIA_STREAMING",
            "name": "High-Volume Media Streaming",
            "desc": "Heavy data transfer or visits to media streaming platforms detected.",
            "severity": "info",
        })

    update_domains = {"update", "apple.com", "googleapis.com", "g.doubleclick.net", "icloud"}
    update_hits = [h for h in hosts_seen if any(u in h for u in update_domains)]
    if update_hits:
        found_tags.append({
            "tag": "SYSTEM_UPDATE",
            "name": "OS & System Syncing",
            "desc": "Device actively synchronizing background telemetry or operating system updates.",
            "severity": "info",
        })

    if total_flows > 50 and total_bytes / max(1, total_flows) < 2048:
        found_tags.append({
            "tag": "PERIODIC_SYNC",
            "name": "Frequent Background Syncs",
            "desc": "Numerous short-lived small flows suggest frequent app telemetry or background polling.",
            "severity": "low",
        })

    out = {
        "total_flows": total_flows,
        "total_packets": total_packets,
        "total_bytes": total_bytes,
        "detected_patterns": found_tags,
    }

    if use_cache:
        _pattern_cache[device_mac] = (time.time(), out)

    return out
