import React from 'react';
import './MonitoringScreen.css';
import DeviceList from '../DeviceList/DeviceList';
import DnsTable from '../DnsTable/DnsTable';
import DnsAnalytics from '../DnsAnalytics/DnsAnalytics';
import TelemetryTables from '../TelemetryTables/TelemetryTables';
import RecommendationsPanel from '../RecommendationsPanel/RecommendationsPanel';
import useWispyData from '../../hooks/useWispyData';
import useRecommendations from '../../hooks/useRecommendations';

const MonitoringScreen = ({ selectedNetwork }) => {
  const {
    devices,
    dnsQueries,
    dnsTotal,
    tlsSni,
    ja3Rows,
    mdnsRows,
    error,
    loadMoreDns,
    loadingMoreDns,
    hasMoreDns,
  } = useWispyData(2000);
  const { recommendations, loading, error: recError, getRecommendations } = useRecommendations();

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

        <DeviceList
          devices={devices}
          dnsQueries={dnsQueries}
          tlsSni={tlsSni}
          ja3Rows={ja3Rows}
          mdnsRows={mdnsRows}
        />
        <TelemetryTables tlsSni={tlsSni} ja3={ja3Rows} mdns={mdnsRows} />
        <DnsAnalytics dnsQueries={dnsQueries} />
        <DnsTable
          dnsQueries={dnsQueries}
          dnsTotal={dnsTotal}
          onLoadMore={loadMoreDns}
          hasMoreDns={hasMoreDns}
          loadingMoreDns={loadingMoreDns}
        />
        <RecommendationsPanel
          recommendations={recommendations}
          loading={loading}
          error={recError}
          onGetRecommendations={getRecommendations}
        />
      </div>
    </div>
  );
};

export default MonitoringScreen;
