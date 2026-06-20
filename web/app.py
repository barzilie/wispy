import os
import sys
import subprocess
import json
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from analysis.storage import (
    get_devices,
    get_dns_requests,
    count_dns_requests,
    get_tls_sni,
    count_tls_sni,
    get_ja3,
    count_ja3,
    get_mdns,
    count_mdns,
    get_flow_sessions,
    count_flow_sessions,
    get_plaintext_events,
    count_plaintext_events,
)
import atexit

ap_processes = []


from config import FLASK_HOST, FLASK_PORT, WIFI_INTERFACE, print_startup_info, get_mode_info
from core.scanner import enable_monitor_mode, scan_networks

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # cors for react dev server

# shared scan/ap state
scan_state = {
    'scanning': False,
    'networks': [],
    'selected_network': None,
    'monitoring': False,
}


@app.route('/')
def index():
    return render_template('index.html')


def _int_arg(name, default, min_v=0, max_v=None):
    try:
        v = int(request.args.get(name, default))
    except (TypeError, ValueError):
        v = default
    if v < min_v:
        v = min_v
    if max_v is not None and v > max_v:
        v = max_v
    return v


@app.route('/api/data')
def api_data():
    """Devices plus optional DNS slice and recent TLS SNI / JA3 / mDNS telemetry."""
    include_dns = request.args.get('include_dns', '1').lower() not in ('0', 'false', 'no')
    dns_limit = _int_arg('dns_limit', 200, min_v=1, max_v=2000)
    dns_offset = _int_arg('dns_offset', 0, min_v=0, max_v=10_000_000)
    tel_lim = _int_arg('telemetry_limit', 200, min_v=1, max_v=2000)
    include_telemetry = request.args.get('include_telemetry', '1').lower() not in ('0', 'false', 'no')

    resp_data = {
        'devices': get_devices(),
        'dns_total': count_dns_requests(),
    }
    if include_dns:
        resp_data['dns'] = get_dns_requests(limit=dns_limit, offset=dns_offset)
    else:
        resp_data['dns'] = []

    if include_telemetry:
        resp_data['tls_sni'] = get_tls_sni(limit=tel_lim, offset=0)
        resp_data['tls_sni_total'] = count_tls_sni()
        resp_data['ja3'] = get_ja3(limit=tel_lim, offset=0)
        resp_data['ja3_total'] = count_ja3()
        resp_data['mdns'] = get_mdns(limit=tel_lim, offset=0)
        resp_data['mdns_total'] = count_mdns()
        resp_data['flows'] = get_flow_sessions(limit=tel_lim, offset=0)
        resp_data['flows_total'] = count_flow_sessions()
        resp_data['plaintext'] = get_plaintext_events(limit=tel_lim, offset=0)
        resp_data['plaintext_total'] = count_plaintext_events()
    else:
        resp_data['tls_sni'] = []
        resp_data['tls_sni_total'] = 0
        resp_data['ja3'] = []
        resp_data['ja3_total'] = 0
        resp_data['mdns'] = []
        resp_data['mdns_total'] = 0
        resp_data['flows'] = []
        resp_data['flows_total'] = 0
        resp_data['plaintext'] = []
        resp_data['plaintext_total'] = 0

    include_patterns = request.args.get('include_patterns', '1').lower() not in ('0', 'false', 'no')
    if include_patterns:
        from analysis.patterns import analyze_device_patterns
        for dev in resp_data['devices']:
            pat_info = analyze_device_patterns(dev['mac'], use_cache=True)
            dev['patterns'] = pat_info['detected_patterns']
            dev['flow_stats'] = {
                'total_flows': pat_info['total_flows'],
                'total_packets': pat_info['total_packets'],
                'total_bytes': pat_info['total_bytes'],
            }

    return jsonify(resp_data)


@app.route('/api/dns')
def api_dns():
    """Paginated / cursor DNS feed for infinite scroll and incremental refresh."""
    limit = _int_arg('limit', 200, min_v=1, max_v=5000)
    offset = _int_arg('offset', 0, min_v=0, max_v=10_000_000)
    device_mac = request.args.get('mac') or request.args.get('device_mac')
    after_id = request.args.get('after_id')
    before_id = request.args.get('before_id')

    after = before = None
    if after_id is not None and str(after_id).strip() != '':
        try:
            after = int(after_id)
        except ValueError:
            after = None
    if before_id is not None and str(before_id).strip() != '':
        try:
            before = int(before_id)
        except ValueError:
            before = None

    rows = get_dns_requests(
        limit=limit,
        offset=offset if after is None and before is None else 0,
        device_mac=device_mac,
        after_id=after,
        before_id=before,
    )
    total = count_dns_requests(device_mac=device_mac)
    return jsonify({
        'dns': rows,
        'total': total,
        'count': len(rows),
    })


@app.route('/api/agent/investigate', methods=['POST'])
def api_agent_investigate():
    try:
        from analysis.agentic import investigate_session
        result = investigate_session()
    except Exception as e:
        result = f'Agent investigation not available: {e}'
    return jsonify({'result': result})


@app.route('/api/agent/recommend', methods=['POST'])
def api_agent_recommend():
    try:
        from analysis.agentic import recommend_attacks
        result = recommend_attacks()
    except Exception as e:
        result = f'Agent recommendation not available: {e}'
    return jsonify({'result': result})


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """Alias for backward compatibility."""
    return api_agent_recommend()



@app.route('/api/start-scan', methods=['POST'])
def start_scan():
    """Start WiFi scanning on the configured interface."""
    global scan_state

    if scan_state['scanning']:
        return jsonify({'status': 'already_scanning'})

    scan_state['scanning'] = True

    try:
        print(f"[*] scanning {WIFI_INTERFACE}...")
        mon_if = enable_monitor_mode(WIFI_INTERFACE)
        networks = scan_networks(mon_if, duration=15)
        for net in networks:
            if 'signal' not in net:
                net['signal'] = -60

        scan_state['networks'] = networks
        scan_state['scanning'] = False

        return jsonify({
            'status': 'complete',
            'networks': networks,
        })

    except Exception as e:
        scan_state['scanning'] = False
        print(f"[error] scan failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
        }), 500


@app.route('/api/networks')
def get_networks():
    """Get scanned networks"""
    return jsonify({
        'scanning': scan_state['scanning'],
        'networks': scan_state['networks']
    })


@app.route('/api/flows')
def api_flows():
    """Paginated / cursor flow session feed."""
    limit = _int_arg('limit', 200, min_v=1, max_v=5000)
    offset = _int_arg('offset', 0, min_v=0, max_v=10_000_000)
    device_mac = request.args.get('mac') or request.args.get('device_mac')
    after_id = request.args.get('after_id')
    before_id = request.args.get('before_id')

    after = before = None
    if after_id is not None and str(after_id).strip() != '':
        try:
            after = int(after_id)
        except ValueError:
            after = None
    if before_id is not None and str(before_id).strip() != '':
        try:
            before = int(before_id)
        except ValueError:
            before = None

    rows = get_flow_sessions(
        limit=limit,
        offset=offset if after is None and before is None else 0,
        device_mac=device_mac,
        after_id=after,
        before_id=before,
    )
    total = count_flow_sessions(device_mac=device_mac)
    return jsonify({
        'flows': rows,
        'total': total,
        'count': len(rows),
    })


@app.route('/api/plaintext')
def api_plaintext():
    """Paginated / cursor plaintext events feed."""
    limit = _int_arg('limit', 200, min_v=1, max_v=5000)
    offset = _int_arg('offset', 0, min_v=0, max_v=10_000_000)
    device_mac = request.args.get('mac') or request.args.get('device_mac')
    after_id = request.args.get('after_id')
    before_id = request.args.get('before_id')

    after = before = None
    if after_id is not None and str(after_id).strip() != '':
        try:
            after = int(after_id)
        except ValueError:
            after = None
    if before_id is not None and str(before_id).strip() != '':
        try:
            before = int(before_id)
        except ValueError:
            before = None

    rows = get_plaintext_events(
        limit=limit,
        offset=offset if after is None and before is None else 0,
        device_mac=device_mac,
        after_id=after,
        before_id=before,
    )
    total = count_plaintext_events(device_mac=device_mac)
    return jsonify({
        'plaintext': rows,
        'total': total,
        'count': len(rows),
    })


def cleanup_ap_processes():
    global ap_processes
    if ap_processes:
        print("[*] killing rogue ap processes...")
        from core.ap_manager import teardown
        outbound_iface = os.getenv("OUTBOUND_INTERFACE", "eth0")
        teardown(ap_processes, interface=WIFI_INTERFACE, outbound_interface=outbound_iface)
        ap_processes = []


atexit.register(cleanup_ap_processes)


def _assert_process_running(proc, name, grace_sec=0.4):
    """Raises if a subprocess exits immediately after start."""
    time.sleep(grace_sec)
    if proc.poll() is not None:
        raise RuntimeError(f"{name} exited immediately (code {proc.returncode}). Check the terminal logs above.")


def _start_sniffer_process(project_root, sniffer_path):
    """Spawn core/sniffer.py; optional passwordless sudo via WISPY_SNIFFER_SUDO."""
    use_sudo = os.getenv("WISPY_SNIFFER_SUDO", "false").lower() == "true"
    cmd = [sys.executable, sniffer_path]
    if use_sudo:
        cmd = ["sudo", "-n"] + cmd
        
    proc = subprocess.Popen(
        cmd,
        cwd=project_root,
        # Send output directly to the terminal running the Flask app
        stdout=sys.stdout, 
        stderr=sys.stderr, 
    )
    _assert_process_running(proc, "Packet sniffer")
    return proc, use_sudo


@app.route('/api/select-network', methods=['POST'])
def select_network():
    """Select a network to attack and deploy the rogue AP on Kali."""
    global scan_state

    data = request.json
    ssid = data.get('ssid')

    # find ssid in last scan results
    picked = next((n for n in scan_state['networks'] if n['ssid'] == ssid), None)

    if not picked:
        return jsonify({'status': 'error', 'message': 'Network not found'}), 404

    scan_state['selected_network'] = picked
    scan_state['monitoring'] = True
    extra = {}

    try:
        from core.scanner import disable_monitor_mode
        from core.ap_manager import configure_interface, write_hostapd_conf, write_dnsmasq_conf, enable_routing, start_hostapd, start_dnsmasq

        mon_if = WIFI_INTERFACE + "mon"
        try:
            disable_monitor_mode(mon_if)
        except Exception as e:
            print(f"[ap] monitor mode disable warning: {e}")

        print(f"[ap] setting up {WIFI_INTERFACE}...")
        configure_interface(WIFI_INTERFACE)

        print("[ap] writing hostapd + dnsmasq configs")
        write_hostapd_conf(picked['ssid'], picked.get('channel', 6), WIFI_INTERFACE)
        write_dnsmasq_conf(WIFI_INTERFACE)

        wan_if = os.getenv("OUTBOUND_INTERFACE", "eth0")
        print(f"[ap] nat on {wan_if}...")
        enable_routing(wan_if)

        print("[ap] starting hostapd and dnsmasq")
        p_hostapd = start_hostapd()
        _assert_process_running(p_hostapd, "hostapd")
        ap_processes.append(p_hostapd)

        p_dnsmasq = start_dnsmasq()
        _assert_process_running(p_dnsmasq, "dnsmasq")
        ap_processes.append(p_dnsmasq)

        print("[ap] starting sniffer subprocess")
        proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        sniffer_script = os.path.join(proj_root, 'core', 'sniffer.py')
        p_sniff, used_sudo = _start_sniffer_process(proj_root, sniffer_script)
        ap_processes.append(p_sniff)

        print("[ap] rogue ap should be up now")
        if not used_sudo:
            extra['sniffer_warning'] = (
                "Sniffer started without root; capture may be empty. "
                "Set WISPY_SNIFFER_SUDO=true in .env (with passwordless sudo for the sniffer), "
                "or run: sudo .venv/bin/python core/sniffer.py"
            )

    except Exception as e:
        print(f"[ap] deploy failed: {e}")
        cleanup_ap_processes()
        scan_state['monitoring'] = False
        scan_state['selected_network'] = None
        return jsonify({'status': 'error', 'message': f'Failed to deploy AP: {e}'}), 500

    body = {'status': 'success', 'network': picked}
    body.update(extra)
    return jsonify(body)


@app.route('/api/stop-ap', methods=['POST'])
def stop_ap():
    """Stop the rogue AP deployment and return to network selection."""
    global scan_state
    cleanup_ap_processes()
    scan_state['monitoring'] = False
    scan_state['selected_network'] = None
    return jsonify({'status': 'success'})



@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'scanning': scan_state['scanning'],
        'monitoring': scan_state['monitoring'],
        'selected_network': scan_state['selected_network'],
        'mode_info': get_mode_info()
    })


if __name__ == '__main__':
    print_startup_info()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
