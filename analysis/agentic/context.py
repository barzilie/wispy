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

    # bulk load so we dont hammer sqlite
    dns = get_dns_requests(limit=4000, offset=0)
    tls = get_tls_sni(limit=2000, offset=0)
    ja3 = get_ja3(limit=2000, offset=0)
    mdns = get_mdns(limit=2000, offset=0)
    flows = get_flow_sessions(limit=2000, offset=0)
    plaintext = get_plaintext_events(limit=2000, offset=0)

    # bucket telemetry by mac
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
            "body_snippet": r["body"][:200] if r.get("body") else ""  # trim body for token limit
        })

    device_rows = []
    for d in devices:
        mac = d["mac"]
        
        # run pattern heuristics
        pat_data = analyze_device_patterns(
            mac,
            query_limit=PATTERN_AGENT_QUERY_LIMIT,
            use_cache=True,
        )
        
        # top dns by count
        doms = dns_by_mac[mac]
        dom_freq = defaultdict(int)
        for dom in doms:
            dom_freq[dom] += 1
        top_domains = sorted(dom_freq.keys(), key=lambda x: dom_freq[x], reverse=True)[:15]

        # same for sni
        sni_vals = tls_by_mac[mac]
        sni_freq = defaultdict(int)
        for s in sni_vals:
            sni_freq[s] += 1
        top_snis = sorted(sni_freq.keys(), key=lambda x: sni_freq[x], reverse=True)[:15]

        device_rows.append({
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
            "recent_flows": flows_by_mac[mac][:30],  # cap flows per device
            "behavior_patterns": pat_data["detected_patterns"],
            "flow_totals": {
                "flows": pat_data["total_flows"],
                "packets": pat_data["total_packets"],
                "bytes": pat_data["total_bytes"]
            },
            "recent_plaintext_events": plaintext_by_mac[mac][:15]
        })

    return {
        "devices": device_rows,
        "total_captured_devices": len(device_rows)
    }
