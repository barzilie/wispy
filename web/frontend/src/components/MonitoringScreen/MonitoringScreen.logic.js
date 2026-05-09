// MonitoringScreen logic

export const calculateUptime = (startTime) => {
  const now = new Date();
  const diff = now - new Date(startTime);
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);
  return `${hours}h ${minutes}m ${seconds}s`;
};

export const getConnectionStatus = (lastUpdate) => {
  const now = new Date();
  const diff = now - new Date(lastUpdate);
  return diff < 5000 ? 'LIVE' : 'STALE';
};
