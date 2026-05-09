import os
import sys
import subprocess
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from analysis.storage import get_devices, get_dns_requests

# Import configuration
from config import MOCK_MODE, FLASK_HOST, FLASK_PORT, WIFI_INTERFACE, print_startup_info, get_mode_info

# Import mock data or real scanner based on mode
if MOCK_MODE:
    from mock.mock_networks import get_mock_networks
else:
    from core.scanner import enable_monitor_mode, scan_networks

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Enable CORS for all routes

# Store scan results and process state
scan_state = {
    'scanning': False,
    'networks': [],
    'selected_network': None,
    'monitoring': False,
    'mock_mode': MOCK_MODE
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data')
def api_data():
    return jsonify({
        'devices': get_devices(),
        'dns':     get_dns_requests(limit=150),
    })


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    try:
        from analysis.recommender import get_recommendations
        result = get_recommendations()
    except Exception as e:
        result = f'Recommender not available: {e}'
    return jsonify({'result': result})


@app.route('/api/start-scan', methods=['POST'])
def start_scan():
    """Start WiFi scanning (mock for macOS, real on Kali)"""
    global scan_state

    if scan_state['scanning']:
        return jsonify({'status': 'already_scanning'})

    scan_state['scanning'] = True

    try:
        if MOCK_MODE:
            # Use mock networks for development
            print("[MOCK MODE] Using mock network data")
            networks = get_mock_networks()
        else:
            # Real scanning on Kali Linux
            print(f"[REAL MODE] Scanning on interface {WIFI_INTERFACE}")
            mon_iface = enable_monitor_mode(WIFI_INTERFACE)
            networks = scan_networks(mon_iface, duration=15)
            # Convert real scan format to match mock format
            for net in networks:
                if 'signal' not in net:
                    net['signal'] = -60  # Default signal if not provided

        scan_state['networks'] = networks
        scan_state['scanning'] = False

        return jsonify({
            'status': 'complete',
            'networks': networks,
            'mock_mode': MOCK_MODE
        })

    except Exception as e:
        scan_state['scanning'] = False
        print(f"[ERROR] Scan failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'mock_mode': MOCK_MODE
        }), 500


@app.route('/api/networks')
def get_networks():
    """Get scanned networks"""
    return jsonify({
        'scanning': scan_state['scanning'],
        'networks': scan_state['networks']
    })


@app.route('/api/select-network', methods=['POST'])
def select_network():
    """Select a network to attack"""
    global scan_state

    data = request.json
    ssid = data.get('ssid')

    # Find the network
    selected = next((n for n in scan_state['networks'] if n['ssid'] == ssid), None)

    if not selected:
        return jsonify({'status': 'error', 'message': 'Network not found'}), 404

    scan_state['selected_network'] = selected
    scan_state['monitoring'] = True

    # On Kali, this would start main.py with the selected network
    # For now, just store the selection

    return jsonify({
        'status': 'success',
        'network': selected
    })


@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'scanning': scan_state['scanning'],
        'monitoring': scan_state['monitoring'],
        'selected_network': scan_state['selected_network'],
        'mock_mode': MOCK_MODE,
        'mode_info': get_mode_info()
    })


if __name__ == '__main__':
    print_startup_info()
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
