import React from 'react';
import './tabs.scss';

const Tabs = ({ children, labelText }) => (
  <div className="pf-c-tabs" aria-label={labelText}>
    <ul className="pf-c-tabs__list">
      {children}
    </ul>
  </div>
);

export default Tabs;
