"""
wispy config stuff - mock mode etc
"""

import os
import platform

# figure out what OS we're on
IS_MACOS = platform.system() == 'Darwin'
IS_KALI = platform.system() == 'Linux' and os.path.exists('/etc/os-release')

# mock mode, override in .env if you want
# defaults to true on mac and false on kali/linux
MOCK_MODE = os.getenv('WISPY_MOCK_MODE', 'true' if IS_MACOS else 'false').lower() == 'true'

# flask host/port
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# wifi iface - only matters when not in mock mode
WIFI_INTERFACE = os.getenv('WIFI_INTERFACE', 'wlan0')

# gemini api key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

def get_mode_info():
    """Get current mode information for display"""
    return {
        'platform': platform.system(),
        'mock_mode': MOCK_MODE,
        'is_macos': IS_MACOS,
        'is_kali': IS_KALI,
        'wifi_interface': WIFI_INTERFACE if not MOCK_MODE else 'N/A'
    }

def print_startup_info():
    """Print startup configuration"""
    print("\n" + "="*60)
    print("WiSpy - network monitoring thing")
    print("="*60)
    print(f"Platform:        {platform.system()}")
    print(f"Mock Mode:       {'ENABLED' if MOCK_MODE else 'DISABLED'}")
    print(f"WiFi Interface:  {WIFI_INTERFACE if not MOCK_MODE else 'mock data'}")
    print(f"Flask Server:    {FLASK_HOST}:{FLASK_PORT}")
    print("="*60 + "\n")
