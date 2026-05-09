// DeviceCard logic and utility functions

export const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp).toLocaleTimeString();
};

export const getDeviceIcon = (osGuess) => {
  const icons = {
    'iOS': '📱',
    'Android': '📱',
    'Windows': '💻',
    'macOS': '💻',
    'Linux': '🖥️',
  };
  return icons[osGuess] || '🖥️';
};
