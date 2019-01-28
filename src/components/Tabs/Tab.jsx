import React from 'react';
import { NavLink } from 'react-router-dom';
import './tabs.scss';

const Tab = ({ children, link, replace }) => (
  <li className="pf-c-tabs__item">
    <NavLink
      to={link}
      replace={replace}
      className="pf-c-tabs__button"
      activeClassName="pf-m-current"
    >
      {children}
    </NavLink>
  </li>
);

export default Tab;
