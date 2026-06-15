import React from 'react';
import './App.css';
import StartScreen from './components/StartScreen/StartScreen';
import NetworkSelectionScreen from './components/NetworkSelectionScreen/NetworkSelectionScreen';
import MonitoringScreen from './components/MonitoringScreen/MonitoringScreen';
import useAppFlow from './hooks/useAppFlow';

function App() {
  const {
    screen,
    networks,
    selectedNetwork,
    loading,
    restoring,
    error,
    startScan,
    selectNetwork,
  } = useAppFlow();

  if (restoring) {
    return (
      <div className="App app-restoring">
        <p>Restoring session…</p>
      </div>
    );
  }

  return (
    <div className="App">
      {error && (
        <div className="error-banner">
          <p>⚠️ ERROR: {error}</p>
        </div>
      )}

      {screen === 'start' && (
        <StartScreen onStartHacking={startScan} loading={loading} />
      )}

      {screen === 'selection' && (
        <NetworkSelectionScreen
          networks={networks}
          onSelectNetwork={selectNetwork}
          loading={loading}
        />
      )}

      {screen === 'monitoring' && (
        <MonitoringScreen selectedNetwork={selectedNetwork} />
      )}
    </div>
  );
}

export default App;
