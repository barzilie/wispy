import { useState, useEffect } from 'react';

const useWispyData = (refreshInterval = 2000) => {
  const [devices, setDevices] = useState([]);
  const [dnsQueries, setDnsQueries] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/data');
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        setDevices(data.devices);
        setDnsQueries(data.dns);
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { devices, dnsQueries, error };
};

export default useWispyData;
