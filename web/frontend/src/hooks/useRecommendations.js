import { useState } from 'react';

const useRecommendations = () => {
  const [recommendations, setRecommendations] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to get recommendations');
      }

      const data = await response.json();
      setRecommendations(data.result);
    } catch (err) {
      console.error('Error getting recommendations:', err);
      setError(err.message);
      setRecommendations('Error: Could not get recommendations');
    } finally {
      setLoading(false);
    }
  };

  return { recommendations, loading, error, getRecommendations };
};

export default useRecommendations;
