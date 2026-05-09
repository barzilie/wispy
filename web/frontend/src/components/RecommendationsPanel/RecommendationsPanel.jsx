import React from 'react';
import './RecommendationsPanel.css';

const RecommendationsPanel = ({ recommendations, loading, onGetRecommendations }) => {
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
      {recommendations && (
        <div className="recommendations-box">
          <pre>{recommendations}</pre>
        </div>
      )}
    </section>
  );
};

export default RecommendationsPanel;
