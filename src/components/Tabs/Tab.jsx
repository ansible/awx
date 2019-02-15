import React from 'react';
import PropTypes from 'prop-types';
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

Tab.propTypes = {
  children: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.node),
    PropTypes.node
  ]).isRequired,
  link: PropTypes.string,
  replace: PropTypes.bool,
};

Tab.defaultProps = {
  link: null,
  replace: false,
};

export default Tab;
