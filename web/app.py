import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, render_template
from analysis.storage import get_devices, get_dns_requests

app = Flask(__name__, template_folder='templates', static_folder='static')


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
