// StartScreen logic

export const validateSystemReady = () => {
  // Check if system is ready to start
  return true;
};

export const formatSystemInfo = () => {
  return {
    os: 'Kali Linux',
    adapter: 'TP-Link TL-WN722N',
    mode: 'Monitor Mode',
    status: 'Ready'
  };
};
