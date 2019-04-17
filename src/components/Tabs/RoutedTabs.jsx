import React from 'react';

import {
  Tab,
  Tabs
} from '@patternfly/react-core';

export default function RoutedTabs (props) {
  const { history, tabsArray } = props;
  const getActiveTabId = () => {
    if (history && history.location.pathname) {
      const matchTab = tabsArray.find(selectedTab => selectedTab.link
        === history.location.pathname);
      return matchTab.id;
    }
    return 0;
  };

  function handleTabSelect (event, eventKey) {
    if (history && history.location.pathname) {
      const tab = tabsArray.find(tabElement => tabElement.id === eventKey);
      history.push(tab.link);
    }
  }

  return (
    <Tabs
      activeKey={getActiveTabId()}
      onSelect={handleTabSelect}
    >
      {tabsArray.map(tabElement => (
        <Tab
          className={`${tabElement.name}`}
          aria-label={`${tabElement.name}`}
          eventKey={tabElement.id}
          key={tabElement.id}
          link={tabElement.link}
          title={tabElement.name}
        />
      ))}
    </Tabs>
  );
}

