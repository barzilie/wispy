// DeviceList logic and utility functions

export const sortDevicesByLastSeen = (devices) => {
  return [...devices].sort((a, b) =>
    new Date(b.last_seen) - new Date(a.last_seen)
  );
};

export const sortDevicesByHostname = (devices) => {
  return [...devices].sort((a, b) =>
    (a.hostname || 'Unknown').localeCompare(b.hostname || 'Unknown')
  );
};

export const filterDevicesByOS = (devices, osType) => {
  if (!osType) return devices;
  return devices.filter(device => device.os_guess === osType);
};

export const getDeviceCount = (devices) => {
  return devices.length;
};

export const getOSBreakdown = (devices) => {
  const breakdown = {};
  devices.forEach(device => {
    const os = device.os_guess || 'Unknown';
    breakdown[os] = (breakdown[os] || 0) + 1;
  });
  return breakdown;
};
