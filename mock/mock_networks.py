"""
Mock WiFi Networks Data
Edit this file to customize mock networks for development
"""

# fake wifi scan results - edit as you like
MOCK_NETWORKS = [
    {
        "ssid": "HomeNetwork_5G",
        "bssid": "00:11:22:33:44:55",
        "channel": 6,
        "encryption": "WPA",
        "signal": -45  # pretty strong
    },
    {
        "ssid": "CoffeeShop_WiFi",
        "bssid": "AA:BB:CC:DD:EE:FF",
        "channel": 11,
        "encryption": "Open",  # no password
        "signal": -65
    },
    {
        "ssid": "Neighbor_Network",
        "bssid": "11:22:33:44:55:66",
        "channel": 1,
        "encryption": "WPA",
        "signal": -70  # meh signal
    },
    {
        "ssid": "Guest_WiFi",
        "bssid": "77:88:99:AA:BB:CC",
        "channel": 3,
        "encryption": "Open",
        "signal": -80  # weak
    },
    {
        "ssid": "Office_Network",
        "bssid": "DD:EE:FF:00:11:22",
        "channel": 9,
        "encryption": "WPA",
        "signal": -55
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


# add more networks below if you want:
# add_mock_network("MyCustomNetwork", "11:22:33:44:55:66", 6, "WPA", -50)
