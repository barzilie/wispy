import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch
from analysis.storage import init_db, upsert_device, insert_dns, get_devices, get_dns_requests, get_session_summary, reset_db

def test_init():
    init_db()
    print("[PASS] init_db")

def test_insert_devices():
    upsert_device('AA:BB:CC:DD:EE:01', ip='192.168.1.10', hostname='Johns-iPhone', vendor='Apple', os_guess='iOS')
    upsert_device('AA:BB:CC:DD:EE:02', ip='192.168.1.11', hostname='DESKTOP-WIN', vendor='Intel', os_guess='Windows')
    devices = get_devices()
    macs = [d['mac'] for d in devices]
    assert 'AA:BB:CC:DD:EE:01' in macs
    assert 'AA:BB:CC:DD:EE:02' in macs
    print("[PASS] insert_devices")

def test_partial_update():
    upsert_device('AA:BB:CC:DD:EE:01', ip='192.168.1.99')
    device = next(d for d in get_devices() if d['mac'] == 'AA:BB:CC:DD:EE:01')
    assert device['ip'] == '192.168.1.99',        f"Expected 192.168.1.99, got {device['ip']}"
    assert device['hostname'] == 'Johns-iPhone',   f"Hostname was wiped: {device['hostname']}"
    assert device['vendor'] == 'Apple',            f"Vendor was wiped: {device['vendor']}"
    assert device['os_guess'] == 'iOS',            f"OS was wiped: {device['os_guess']}"
    print("[PASS] partial_update (COALESCE check)")

def test_insert_dns():
    insert_dns('AA:BB:CC:DD:EE:01', 'api.instagram.com')
    insert_dns('AA:BB:CC:DD:EE:01', 'graph.facebook.com')
    insert_dns('AA:BB:CC:DD:EE:01', 'api.spotify.com')
    insert_dns('AA:BB:CC:DD:EE:02', 'outlook.office365.com')
    insert_dns('AA:BB:CC:DD:EE:02', 'slack.com')
    records = get_dns_requests()
    assert len(records) >= 5
    domains = [r['domain'] for r in records]
    assert 'api.instagram.com' in domains
    assert 'slack.com' in domains
    print("[PASS] insert_dns")

def test_session_summary():
    summary = get_session_summary()
    assert len(summary) >= 2
    iphone = next(s for s in summary if s['mac'] == 'AA:BB:CC:DD:EE:01')
    assert 'api.spotify.com' in iphone['domains_queried']
    assert 'api.instagram.com' in iphone['domains_queried']
    desktop = next(s for s in summary if s['mac'] == 'AA:BB:CC:DD:EE:02')
    assert 'slack.com' in desktop['domains_queried']
    print("[PASS] session_summary")

def test_dns_limit():
    for i in range(20):
        insert_dns('AA:BB:CC:DD:EE:01', f'test-domain-{i}.com')
    records = get_dns_requests(limit=5)
    assert len(records) == 5
    print("[PASS] dns_limit")

def test_reset_confirmed():
    with patch('builtins.input', return_value='yes'):
        reset_db()
    assert get_devices() == []
    assert get_dns_requests() == []
    print("[PASS] reset_db (confirmed)")

def test_reset_cancelled():
    upsert_device('AA:BB:CC:DD:EE:03', ip='192.168.1.20')
    with patch('builtins.input', return_value='no'):
        reset_db()
    devices = get_devices()
    assert any(d['mac'] == 'AA:BB:CC:DD:EE:03' for d in devices)
    print("[PASS] reset_db (cancelled — data intact)")

if __name__ == '__main__':
    print("Running storage tests...\n")
    test_init()
    test_insert_devices()
    test_partial_update()
    test_insert_dns()
    test_session_summary()
    test_dns_limit()
    test_reset_confirmed()
    test_reset_cancelled()
    print("\nAll tests passed.")
