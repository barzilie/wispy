import React, { useState } from 'react';
import './RecommendationsPanel.css';

const RecommendationsPanel = ({ 
  investigation = '', 
  recommendations = '', 
  loading = false, 
  error = null, 
  onGetInvestigation, 
  onGetRecommendations 
}) => {
  // Tracks which content to show in the box below the buttons
  const [activeView, setActiveView] = useState('investigate');

  const handleInvestigateClick = () => {
    setActiveView('investigate');
    onGetInvestigation();
  };

  const handleRecommendClick = () => {
    setActiveView('recommend');
    onGetRecommendations();
  };

  const activeContent = activeView === 'investigate' ? investigation : recommendations;
  const boxHeader = activeView === 'investigate' ? '[ SESSION COGNITIVE ANALYSIS ]' : '[ ATTACK VECTOR ANALYSIS ]';

  return (
    <section className="section">
      <h2>🤖 Agentic AI analysis</h2>
      
      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
        <button
          onClick={handleInvestigateClick}
          disabled={loading}
          className={`recommend-button ${activeView === 'investigate' ? 'tab-active' : 'tab-inactive'}`}
        >
          {loading && activeView === 'investigate' ? 'Analyzing...' : 'Investigate Session'}
        </button>
        
        <button
          onClick={handleRecommendClick}
          disabled={loading}
          className={`recommend-button ${activeView === 'recommend' ? 'tab-active' : 'tab-inactive'}`}
        >
          {loading && activeView === 'recommend' ? 'Analyzing...' : 'Suggest Next Steps'}
        </button>
      </div>

      {error && (
        <div className="recommendations-error" role="alert">
          {error}
        </div>
      )}

      {activeContent && (
        <div className="recommendations-box">
          <span className="box-header-title">{boxHeader}</span>
          <pre>{activeContent}</pre>
        </div>
      )}
    </section>
  );
};

export default RecommendationsPanel;