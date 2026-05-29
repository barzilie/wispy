// FlowAnalytics Logic

export const formatBytes = (bytes) => {
  if (bytes == null || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getHostBadgeClass = (source) => {
  if (source === 'sni') return 'badge-sni';
  if (source === 'dns') return 'badge-dns';
  return 'badge-unknown';
};

export const formatTimestamp = (isoString) => {
  if (!isoString) return '';
  try {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (e) {
    return isoString;
  }
};
