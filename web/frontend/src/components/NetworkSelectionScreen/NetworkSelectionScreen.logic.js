// NetworkSelectionScreen logic

export const getSignalStrength = (signal) => {
  // signal is in dBm (negative values, closer to 0 is stronger)
  if (signal >= -50) return '▰▰▰▰▰'; // Excellent
  if (signal >= -60) return '▰▰▰▰▱'; // Good
  if (signal >= -70) return '▰▰▰▱▱'; // Fair
  if (signal >= -80) return '▰▰▱▱▱'; // Weak
  return '▰▱▱▱▱'; // Very Weak
};

export const getEncryptionIcon = (encryption) => {
  if (encryption === 'Open') return '🔓';
  return '🔒';
};

export const sortNetworksBySignal = (networks) => {
  return [...networks].sort((a, b) => b.signal - a.signal);
};

export const filterOpenNetworks = (networks) => {
  return networks.filter(n => n.encryption === 'Open');
};

export const formatNetworkInfo = (network) => {
  return {
    ...network,
    signalQuality: getSignalStrength(network.signal),
    isOpen: network.encryption === 'Open'
  };
};
