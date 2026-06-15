"""
Tests for TA extension features: flow sessions, plaintext events, DNS correlation, patterns.
"""
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis import correlation
from analysis.patterns import analyze_device_patterns
from analysis.storage import (
    init_db,
    upsert_flow_session,
    get_flow_sessions,
    count_flow_sessions,
    insert_plaintext,
    get_plaintext_events,
    count_plaintext_events,
    insert_dns,
    reset_db,
)


MAC = 'AA:BB:CC:DD:EE:99'
NOW = datetime.utcnow().isoformat()
EARLIER = (datetime.utcnow() - timedelta(seconds=5)).isoformat()


def _reset():
    with patch('builtins.input', return_value='yes'):
        reset_db()
    init_db()
    correlation._dns_ip_cache.clear()


def test_flow_session_insert_and_aggregate():
    _reset()
    upsert_flow_session(
        MAC, 'TCP', '192.168.50.10', '142.251.157.119', 443,
        'www.google.com', 'dns', 5, 1200, EARLIER, EARLIER, 'HTTPS',
    )
    upsert_flow_session(
        MAC, 'TCP', '192.168.50.10', '142.251.157.119', 443,
        'www.google.com', 'dns', 3, 800, NOW, NOW, 'HTTPS',
    )
    rows = get_flow_sessions(device_mac=MAC)
    assert len(rows) == 1
    assert rows[0]['packet_count'] == 8
    assert rows[0]['byte_count'] == 2000
    assert rows[0]['dst_host'] == 'www.google.com'
    assert rows[0]['host_source'] == 'dns'
    print('[pass] flow_session_insert_and_aggregate')


def test_flow_session_pagination():
    _reset()
    for i in range(12):
        upsert_flow_session(
            MAC, 'UDP', f'192.168.50.{i}', f'8.8.8.{i}', 53,
            f'host{i}.example.com', 'unknown', 1, 100,
            NOW, NOW, None,
        )
    assert count_flow_sessions() >= 12
    page = get_flow_sessions(limit=5, offset=0)
    assert len(page) == 5
    print('[pass] flow_session_pagination')


def test_plaintext_insert_and_pagination():
    _reset()
    insert_plaintext(MAC, 'http', 'insecure.portal.local', 'GET', 'GET /login HTTP/1.1\r\nHost: insecure.portal.local')
    insert_plaintext(MAC, 'smtp', 'mail.example.com', 'EHLO', '220 mail.example.com ESMTP')
    rows = get_plaintext_events(device_mac=MAC)
    assert len(rows) == 2
    protos = {r['proto'] for r in rows}
    assert protos == {'http', 'smtp'}
    assert count_plaintext_events(device_mac=MAC) == 2
    limited = get_plaintext_events(limit=1, device_mac=MAC)
    assert len(limited) == 1
    print('[pass] plaintext_insert_and_pagination')


def test_dns_correlation_cache():
    correlation._dns_ip_cache.clear()
    correlation.add_dns_mapping(MAC, '157.240.214.61', 'g.whatsapp.net')
    host, source = correlation.resolve_ip_to_host(MAC, '157.240.214.61')
    assert host == 'g.whatsapp.net'
    assert source == 'dns'
    unknown_host, unknown_source = correlation.resolve_ip_to_host(MAC, '1.2.3.4')
    assert unknown_host is None
    assert unknown_source == 'unknown'
    print('[pass] dns_correlation_cache')


def test_device_patterns_heuristics():
    _reset()
    insert_dns(MAC, 'api.instagram.com')
    upsert_flow_session(
        MAC, 'TCP', '192.168.50.10', '157.240.214.61', 443,
        'instagram.com', 'sni', 10, 50000, EARLIER, NOW, 'HTTPS',
    )
    insert_plaintext(MAC, 'http', 'legacy.device.local', 'GET', 'GET / HTTP/1.1')
    result = analyze_device_patterns(MAC)
    assert result['total_flows'] >= 1
    tags = {p['tag'] for p in result['detected_patterns']}
    assert 'PLAINTEXT_LEAKS' in tags
    assert 'SOCIAL_MEDIA' in tags
    print('[pass] device_patterns_heuristics')


if __name__ == '__main__':
    print('running extension tests\n')
    test_flow_session_insert_and_aggregate()
    test_flow_session_pagination()
    test_plaintext_insert_and_pagination()
    test_dns_correlation_cache()
    test_device_patterns_heuristics()
    print('\nall extension tests passed')
