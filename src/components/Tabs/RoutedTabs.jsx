import React from 'react';
import { shape, string, number, arrayOf } from 'prop-types';
import { Tab, Tabs } from '@patternfly/react-core';
import { withRouter } from 'react-router-dom';

function RoutedTabs (props) {
  const { history, tabsArray } = props;

  const getActiveTabId = () => {
    const match = tabsArray.find(tab => tab.link === history.location.pathname);
    if (match) {
      return match.id;
    }
    return 0;
  };

  function handleTabSelect (event, eventKey) {
    const match = tabsArray.find(tab => tab.id === eventKey);
    if (match) {
      history.push(match.link);
    }
  }

  return (
    <Tabs
      activeKey={getActiveTabId()}
      onSelect={handleTabSelect}
    >
      {tabsArray.map(tab => (
        <Tab
          className={`${tab.name}`}
          aria-label={`${tab.name}`}
          eventKey={tab.id}
          key={tab.id}
          link={tab.link}
          title={tab.name}
        />
      ))}
    </Tabs>
  );
}
RoutedTabs.propTypes = {
  history: shape({
    location: shape({
      pathname: string.isRequired
    }).isRequired,
  }).isRequired,
  tabsArray: arrayOf(shape({
    id: number.isRequired,
    link: string.isRequired,
    name: string.isRequired,
  })).isRequired,
};

export { RoutedTabs as _RoutedTabs };
export default withRouter(RoutedTabs);
