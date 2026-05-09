# Mock Data Configuration

This directory contains mock data used for development on macOS (or any non-Kali system).

## How It Works

WiSpy automatically detects your platform:
- **macOS** → Mock mode enabled (uses fake data)
- **Kali Linux** → Real mode enabled (uses actual wireless scanner)

## Mock Mode Control

### Option 1: Automatic (Recommended)
Let WiSpy auto-detect your platform. No configuration needed!

### Option 2: Manual Override
Set the `WISPY_MOCK_MODE` environment variable in `.env`:

```bash
# Force mock mode (useful for testing on Kali)
WISPY_MOCK_MODE=true

# Force real mode (not recommended on macOS)
WISPY_MOCK_MODE=false
```

## Editing Mock Networks

Edit `mock_networks.py` to customize the WiFi networks that appear during scanning:

```python
MOCK_NETWORKS = [
    {
        "ssid": "MyNetwork",           # Network name
        "bssid": "00:11:22:33:44:55",  # MAC address
        "channel": 6,                   # WiFi channel (1-13)
        "encryption": "WPA",            # "Open" or "WPA"
        "signal": -45                   # Signal strength (dBm)
    },
    # Add more networks here...
]
```

### Signal Strength Guide
- `-30 to -50` dBm: Excellent signal
- `-50 to -60` dBm: Very good signal
- `-60 to -70` dBm: Good signal
- `-70 to -80` dBm: Fair signal (weak)
- `-80 to -90` dBm: Poor signal (very weak)

## Adding Custom Networks

You can add networks programmatically:

```python
from mock.mock_networks import add_mock_network

add_mock_network(
    ssid="TestNetwork",
    bssid="AA:BB:CC:DD:EE:FF",
    channel=11,
    encryption="Open",
    signal=-55
)
```

## Testing Mock vs Real Mode

**On macOS (Mock Mode):**
```bash
python web/app.py
# Output: Mock Mode: ENABLED
```

**On Kali (Real Mode):**
```bash
sudo python web/app.py
# Output: Mock Mode: DISABLED
# Will actually scan WiFi networks
```

**Force Mock Mode (for testing):**
```bash
WISPY_MOCK_MODE=true python web/app.py
```

## API Response

The `/api/status` endpoint shows current mode:

```json
{
  "mock_mode": true,
  "mode_info": {
    "platform": "Darwin",
    "mock_mode": true,
    "is_macos": true,
    "is_kali": false,
    "wifi_interface": "N/A"
  }
}
```
