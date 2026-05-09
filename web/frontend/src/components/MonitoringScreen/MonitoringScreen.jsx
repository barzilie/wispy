import React from 'react';
import './MonitoringScreen.css';
import DeviceList from '../DeviceList/DeviceList';
import DnsTable from '../DnsTable/DnsTable';
import RecommendationsPanel from '../RecommendationsPanel/RecommendationsPanel';
import useWispyData from '../../hooks/useWispyData';
import useRecommendations from '../../hooks/useRecommendations';

const MonitoringScreen = ({ selectedNetwork }) => {
  const { devices, dnsQueries, error } = useWispyData(2000);
  const { recommendations, loading, getRecommendations } = useRecommendations();

  return (
    <div className="monitoring-screen">
      <div className="monitoring-header">
        <h1>[ MONITORING ACTIVE ]</h1>
        {selectedNetwork && (
          <div className="target-info">
            <span>TARGET: {selectedNetwork.ssid}</span>
            <span>CH: {selectedNetwork.channel}</span>
            <span className="status-indicator">● LIVE</span>
          </div>
        )}
      </div>

      <div className="container">
        {error && (
          <div className="error-message">
            <p>⚠️ Error: {error}</p>
          </div>
        )}

        <DeviceList devices={devices} />
        <DnsTable dnsQueries={dnsQueries} />
        <RecommendationsPanel
          recommendations={recommendations}
          loading={loading}
          onGetRecommendations={getRecommendations}
        />
      </div>
    </div>
  );
};

export default MonitoringScreen;
