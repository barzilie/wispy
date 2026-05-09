import React from 'react';
import './RecommendationsPanel.css';

const RecommendationsPanel = ({ recommendations, loading, error, onGetRecommendations }) => {
  return (
    <section className="section">
      <h2>🎯 AI Attack Recommendations</h2>
      <button
        onClick={onGetRecommendations}
        disabled={loading}
        className="recommend-button"
      >
        {loading ? 'Analyzing...' : 'Get Recommendations'}
      </button>
      {error && (
        <div className="recommendations-error" role="alert">
          {error}
        </div>
      )}
      {recommendations && (
        <div className="recommendations-box">
          <pre>{recommendations}</pre>
        </div>
      )}
    </section>
  );
};

export default RecommendationsPanel;
