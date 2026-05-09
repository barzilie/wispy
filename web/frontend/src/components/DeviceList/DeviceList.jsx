import React from 'react';
import DeviceCard from '../DeviceCard/DeviceCard';
import './DeviceList.css';
import { getDeviceCount } from './DeviceList.logic';

const DeviceList = ({ devices }) => {
  return (
    <section className="section">
      <h2>📱 Connected Devices ({getDeviceCount(devices)})</h2>
      <div className="devices-grid">
        {devices.map((device) => (
          <DeviceCard key={device.mac} device={device} />
        ))}
      </div>
    </section>
  );
};

export default DeviceList;
