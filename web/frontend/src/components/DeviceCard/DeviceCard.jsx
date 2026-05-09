import React from 'react';
import './DeviceCard.css';
import { formatTimestamp } from './DeviceCard.logic';

const DeviceCard = ({ device }) => {
  return (
    <div className="device-card">
      <div className="device-header">
        <span className="device-name">{device.hostname || 'Unknown Device'}</span>
        <span className="device-os">{device.os_guess}</span>
      </div>
      <div className="device-info">
        <p><strong>MAC:</strong> {device.mac}</p>
        <p><strong>IP:</strong> {device.ip}</p>
        <p><strong>Vendor:</strong> {device.vendor}</p>
        <p><strong>First Seen:</strong> {formatTimestamp(device.first_seen)}</p>
        <p><strong>Last Seen:</strong> {formatTimestamp(device.last_seen)}</p>
      </div>
    </div>
  );
};

export default DeviceCard;
