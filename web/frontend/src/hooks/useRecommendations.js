import { useState } from 'react';

const useRecommendations = () => {
  const [investigation, setInvestigation] = useState('');
  const [recommendations, setRecommendations] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getInvestigation = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/agent/investigate', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to run session investigation');
      }

      const data = await response.json();
      setInvestigation(data.result);
    } catch (err) {
      console.error('Error getting investigation:', err);
      setError(err.message);
      setInvestigation('Error: Could not get session investigation');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/agent/recommend', {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to get attack recommendations');
      }

      const data = await response.json();
      setRecommendations(data.result);
    } catch (err) {
      console.error('Error getting recommendations:', err);
      setError(err.message);
      setRecommendations('Error: Could not get attack recommendations');
    } finally {
      setLoading(false);
    }
  };

  return {
    investigation,
    recommendations,
    loading,
    error,
    getInvestigation,
    getRecommendations,
  };
};

export default useRecommendations;
