"""
wispy config
"""

import os
import platform

IS_KALI = platform.system() == 'Linux' and os.path.exists('/etc/os-release')

FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

WIFI_INTERFACE = os.getenv('WIFI_INTERFACE', 'wlan0')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

def get_mode_info():
    """Get current mode information for display"""
    return {
        'platform': platform.system(),
        'is_kali': IS_KALI,
        'wifi_interface': WIFI_INTERFACE,
    }

def print_startup_info():
    """Print startup configuration"""
    print("\n" + "="*60)
    print("WiSpy - network monitoring")
    print("="*60)
    print(f"Platform:        {platform.system()}")
    print(f"WiFi Interface:  {WIFI_INTERFACE}")
    print(f"Flask Server:    {FLASK_HOST}:{FLASK_PORT}")
    print("="*60 + "\n")
