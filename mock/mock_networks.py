"""
Mock WiFi Networks Data
Edit this file to customize mock networks for development
"""

# Mock networks that appear when scanning
# You can add, remove, or modify these as needed
MOCK_NETWORKS = [
    {
        "ssid": "HomeNetwork_5G",
        "bssid": "00:11:22:33:44:55",
        "channel": 6,
        "encryption": "WPA",
        "signal": -45  # Excellent signal
    },
    {
        "ssid": "CoffeeShop_WiFi",
        "bssid": "AA:BB:CC:DD:EE:FF",
        "channel": 11,
        "encryption": "Open",  # Open network (easier target)
        "signal": -65  # Good signal
    },
    {
        "ssid": "Neighbor_Network",
        "bssid": "11:22:33:44:55:66",
        "channel": 1,
        "encryption": "WPA",
        "signal": -70  # Fair signal
    },
    {
        "ssid": "Guest_WiFi",
        "bssid": "77:88:99:AA:BB:CC",
        "channel": 3,
        "encryption": "Open",
        "signal": -80  # Weak signal
    },
    {
        "ssid": "Office_Network",
        "bssid": "DD:EE:FF:00:11:22",
        "channel": 9,
        "encryption": "WPA",
        "signal": -55  # Very good signal
    },
    {
        "ssid": "Airport_Public",
        "bssid": "33:44:55:66:77:88",
        "channel": 4,
        "encryption": "Open",
        "signal": -75
    }
]


def get_mock_networks():
    """Get the list of mock networks"""
    return MOCK_NETWORKS


def add_mock_network(ssid, bssid, channel, encryption="WPA", signal=-60):
    """
    Add a custom mock network

    Args:
        ssid: Network name
        bssid: MAC address (format: "XX:XX:XX:XX:XX:XX")
        channel: WiFi channel (1-13)
        encryption: "Open" or "WPA"
        signal: Signal strength in dBm (-30 to -90, closer to 0 is stronger)
    """
    MOCK_NETWORKS.append({
        "ssid": ssid,
        "bssid": bssid,
        "channel": channel,
        "encryption": encryption,
        "signal": signal
    })
    return MOCK_NETWORKS


# You can add more mock networks here if needed:
# add_mock_network("MyCustomNetwork", "11:22:33:44:55:66", 6, "WPA", -50)
