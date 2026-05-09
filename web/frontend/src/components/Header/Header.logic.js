// Header logic and utility functions

export const getStatusMessage = () => {
  return 'Network Activity Monitoring & Attack Recommendation System';
};

export const formatTitle = (title) => {
  return title || 'WiSpy Dashboard';
};

// Future: Add functions for live status, connection indicators, etc.
export const getConnectionStatus = () => {
  // Will be used to show if backend is connected
  return 'connected';
};
