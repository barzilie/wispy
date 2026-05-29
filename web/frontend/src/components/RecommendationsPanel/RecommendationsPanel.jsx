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
  const [activeTab, setActiveTab] = useState('investigate'); // 'investigate' or 'recommend'

  const activeContent = activeTab === 'investigate' ? investigation : recommendations;
  const triggerAction = activeTab === 'investigate' ? onGetInvestigation : onGetRecommendations;
  const buttonText = activeTab === 'investigate' ? 'Investigate Session' : 'Suggest Next Steps';
  const boxHeader = activeTab === 'investigate' ? '[ SESSION COGNITIVE ANALYSIS ]' : '[ ATTACK VECTOR ANALYSIS ]';

  return (
    <section className="section">
      <h2>🤖 Agentic AI analysis</h2>
      
      <div className="agentic-tabs" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem' }}>
        <button
          onClick={() => setActiveTab('investigate')}
          className={`recommend-button ${activeTab === 'investigate' ? 'tab-active' : 'tab-inactive'}`}
          style={{ padding: '0.75rem 1.5rem', fontSize: '0.95rem' }}
        >
          Session Investigation
        </button>
        <button
          onClick={() => setActiveTab('recommend')}
          className={`recommend-button ${activeTab === 'recommend' ? 'tab-active' : 'tab-inactive'}`}
          style={{ padding: '0.75rem 1.5rem', fontSize: '0.95rem' }}
        >
          Attack Suggestions
        </button>
      </div>

      <button
        onClick={triggerAction}
        disabled={loading}
        className="recommend-button"
      >
        {loading ? 'Analyzing...' : buttonText}
      </button>

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
