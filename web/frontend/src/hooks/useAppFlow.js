import { useState } from 'react';

const useAppFlow = () => {
  const [screen, setScreen] = useState('start'); // 'start', 'selection', 'monitoring'
  const [networks, setNetworks] = useState([]);
  const [selectedNetwork, setSelectedNetwork] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startScan = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/start-scan', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to start scan');
      }

      const data = await response.json();
      setNetworks(data.networks);
      setScreen('selection');
    } catch (err) {
      console.error('Error starting scan:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const selectNetwork = async (ssid) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/select-network', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ssid }),
      });

      if (!response.ok) {
        throw new Error('Failed to select network');
      }

      const data = await response.json();
      setSelectedNetwork(data.network);

      // Delay before switching to monitoring screen (simulate AP setup)
      setTimeout(() => {
        setScreen('monitoring');
        setLoading(false);
      }, 2000);
    } catch (err) {
      console.error('Error selecting network:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  return {
    screen,
    networks,
    selectedNetwork,
    loading,
    error,
    startScan,
    selectNetwork,
  };
};

export default useAppFlow;
