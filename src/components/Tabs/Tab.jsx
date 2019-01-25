import React from 'react';
import { Link } from 'react-router-dom';

import './tabs.scss';

const Tab = ({ location, match, tab, currentTab, children, breadcrumb }) => {
  const tabClasses = () => {
    let classes = 'pf-c-tabs__item';
    if (tab === currentTab) {
      classes += ' pf-m-current';
    }

    return classes;
  };

  const tabParams = () => {
    const params = new URLSearchParams(location.search);
    if (params.get('tab') !== undefined) {
      params.set('tab', tab);
    } else {
      params.append('tab', tab);
    }

    return `?${params.toString()}`;
  };

  return (
    <li className={tabClasses()}>
      <Link
        className="pf-c-tabs__button"
        to={{ pathname: `${match.url}`, search: tabParams(), state: { breadcrumb } }}
        replace={tab === currentTab}
      >
        {children}
      </Link>
    </li>
  );
};

export default Tab;
