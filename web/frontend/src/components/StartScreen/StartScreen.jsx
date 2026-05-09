import React from 'react';
import './StartScreen.css';

const StartScreen = ({ onStartHacking, loading }) => {
  return (
    <div className="start-screen">
      <div className="start-container">
        <div className="ascii-art">
          <pre>{`
██╗    ██╗██╗███████╗██████╗ ██╗   ██╗
██║    ██║██║██╔════╝██╔══██╗╚██╗ ██╔╝
██║ █╗ ██║██║███████╗██████╔╝ ╚████╔╝
██║███╗██║██║╚════██║██╔═══╝   ╚██╔╝
╚███╔███╔╝██║███████║██║        ██║
 ╚══╝╚══╝ ╚═╝╚══════╝╚═╝        ╚═╝
          `}</pre>
        </div>

        <h1 className="start-title">NETWORK SURVEILLANCE SYSTEM</h1>
        <p className="start-subtitle">[ WIRELESS INTRUSION PLATFORM ]</p>

        <div className="start-info">
          <p>▸ Rogue Access Point Deployment</p>
          <p>▸ Real-Time Traffic Monitoring</p>
          <p>▸ Device Fingerprinting</p>
          <p>▸ AI Attack Vector Analysis</p>
        </div>

        <button
          className="start-button"
          onClick={onStartHacking}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="loading-spinner">◢◣◤◥</span> SCANNING FOR NETWORKS...
            </>
          ) : (
            <>▸ INITIATE SCAN</>
          )}
        </button>

        <div className="start-warning">
          <p>⚠ WARNING: AUTHORIZED USE ONLY</p>
          <p>This tool is for educational and authorized security testing purposes.</p>
        </div>
      </div>
    </div>
  );
};

export default StartScreen;
