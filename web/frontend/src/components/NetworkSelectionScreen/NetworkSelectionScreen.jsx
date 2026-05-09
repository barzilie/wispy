import React from 'react';
import './NetworkSelectionScreen.css';
import { getSignalStrength, getEncryptionIcon } from './NetworkSelectionScreen.logic';

const NetworkSelectionScreen = ({ networks, onSelectNetwork, loading }) => {
  return (
    <div className="network-selection-screen">
      <div className="network-container">
        <h1 className="network-title">[ AVAILABLE NETWORKS DETECTED ]</h1>
        <p className="network-subtitle">▸ Select target network for rogue AP deployment</p>

        <div className="networks-list">
          {networks.length === 0 ? (
            <div className="no-networks">
              <p>◢ NO NETWORKS DETECTED</p>
              <p>Check wireless adapter and try again...</p>
            </div>
          ) : (
            networks.map((network, index) => (
              <div
                key={network.bssid}
                className="network-item"
                onClick={() => !loading && onSelectNetwork(network.ssid)}
              >
                <div className="network-header">
                  <span className="network-index">[{String(index + 1).padStart(2, '0')}]</span>
                  <span className="network-ssid">{network.ssid}</span>
                  <span className="network-signal">{getSignalStrength(network.signal)}</span>
                </div>
                <div className="network-details">
                  <span className="network-detail">
                    <strong>BSSID:</strong> {network.bssid}
                  </span>
                  <span className="network-detail">
                    <strong>CH:</strong> {network.channel}
                  </span>
                  <span className="network-detail">
                    <strong>ENC:</strong> {getEncryptionIcon(network.encryption)} {network.encryption}
                  </span>
                  <span className="network-detail">
                    <strong>PWR:</strong> {network.signal} dBm
                  </span>
                </div>
                <div className="network-action">
                  ▸ CLICK TO SELECT TARGET
                </div>
              </div>
            ))
          )}
        </div>

        {loading && (
          <div className="loading-overlay">
            <div className="loading-message">
              <p>◢◣◤◥ DEPLOYING ROGUE ACCESS POINT...</p>
              <p>Configuring network interface...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NetworkSelectionScreen;
