"""
Context compilation module for constructing structured JSON payloads for the AI agent.
"""
from collections import defaultdict
from analysis.storage import (
    get_devices,
    get_dns_requests,
    get_tls_sni,
    get_ja3,
    get_mdns,
    get_flow_sessions,
    get_plaintext_events,
)
from analysis.patterns import analyze_device_patterns, PATTERN_AGENT_QUERY_LIMIT


def build_agent_context():
    """Builds a complete, structured context dictionary of the current interception session."""
    devices = get_devices()
    if not devices:
        return {}

    # Load data in bulk to minimize queries
    dns = get_dns_requests(limit=4000, offset=0)
    tls = get_tls_sni(limit=2000, offset=0)
    ja3 = get_ja3(limit=2000, offset=0)
    mdns = get_mdns(limit=2000, offset=0)
    flows = get_flow_sessions(limit=2000, offset=0)
    plaintext = get_plaintext_events(limit=2000, offset=0)

    # Group by device MAC
    dns_by_mac = defaultdict(list)
    for r in dns:
        if r.get("domain"):
            dns_by_mac[r["device_mac"]].append(r["domain"])

    tls_by_mac = defaultdict(list)
    for r in tls:
        if r.get("sni"):
            tls_by_mac[r["device_mac"]].append(r["sni"])

    ja3_by_mac = defaultdict(set)
    for r in ja3:
        if r.get("ja3_hash"):
            ja3_by_mac[r["device_mac"]].add(r["ja3_hash"])

    mdns_by_mac = defaultdict(set)
    for r in mdns:
        if r.get("service_name"):
            mdns_by_mac[r["device_mac"]].add(r["service_name"])

    flows_by_mac = defaultdict(list)
    for r in flows:
        flows_by_mac[r["device_mac"]].append({
            "proto": r["proto"],
            "dst_ip": r["dst_ip"],
            "dst_port": r["dst_port"],
            "dst_host": r["dst_host"],
            "host_source": r["host_source"],
            "packets": r["packet_count"],
            "bytes": r["byte_count"],
            "label": r["service_label"]
        })

    plaintext_by_mac = defaultdict(list)
    for r in plaintext:
        plaintext_by_mac[r["device_mac"]].append({
            "proto": r["proto"],
            "host_or_server": r["host_or_server"],
            "command": r["method_or_command"],
            "body_snippet": r["body"][:200] if r.get("body") else ""  # Send body snippet to keep prompt token size small
        })

    compiled_devices = []
    for d in devices:
        mac = d["mac"]
        
        # Analyze behavioral heuristics
        patterns_info = analyze_device_patterns(
            mac,
            query_limit=PATTERN_AGENT_QUERY_LIMIT,
            use_cache=True,
        )
        
        # Get top domains (frequency count)
        domains = dns_by_mac[mac]
        domain_counts = defaultdict(int)
        for dom in domains:
            domain_counts[dom] += 1
        top_domains = sorted(domain_counts.keys(), key=lambda x: domain_counts[x], reverse=True)[:15]

        # Get top SNIs
        snis = tls_by_mac[mac]
        sni_counts = defaultdict(int)
        for s in snis:
            sni_counts[s] += 1
        top_snis = sorted(sni_counts.keys(), key=lambda x: sni_counts[x], reverse=True)[:15]

        compiled_devices.append({
            "mac": mac,
            "ip": d["ip"],
            "hostname": d["hostname"],
            "vendor": d["vendor"],
            "os_guess": d["os_guess"],
            "dhcp_params": d.get("dhcp_params"),
            "top_domains_dns": top_domains,
            "top_tls_sni": top_snis,
            "ja3_fingerprints": list(ja3_by_mac[mac]),
            "mdns_services": list(mdns_by_mac[mac]),
            "recent_flows": flows_by_mac[mac][:30],  # limit to recent 30 flows per device
            "behavior_patterns": patterns_info["detected_patterns"],
            "flow_totals": {
                "flows": patterns_info["total_flows"],
                "packets": patterns_info["total_packets"],
                "bytes": patterns_info["total_bytes"]
            },
            "recent_plaintext_events": plaintext_by_mac[mac][:15]
        })

    return {
        "devices": compiled_devices,
        "total_captured_devices": len(compiled_devices)
    }
