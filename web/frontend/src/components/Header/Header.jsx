import React from 'react';
import './Header.css';
import { getStatusMessage, formatTitle } from './Header.logic';

const Header = () => {
  return (
    <header className="app-header">
      <h1>🕵️ {formatTitle('WiSpy Dashboard')}</h1>
      <p>{getStatusMessage()}</p>
    </header>
  );
};

export default Header;
