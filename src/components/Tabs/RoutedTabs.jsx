import React from 'react';

import {
  withRouter
} from 'react-router-dom';

import {
  Tab,
  Tabs
} from '@patternfly/react-core';

class RoutedTabs extends React.Component {
  constructor (props) {
    super(props);

    this.handleTabSelect = this.handleTabSelect.bind(this);
  }

  getActiveTabId () {
    const { history, tabsArray } = this.props;
    const matchTab = tabsArray.find(selectedTab => selectedTab.link === history.location.pathname);
    return matchTab ? matchTab.id : 0;
  }

  handleTabSelect (event, eventKey) {
    const { history, tabsArray } = this.props;

    const tab = tabsArray.find(tabElement => tabElement.id === eventKey);
    history.push(tab.link);
  }

  render () {
    const { tabsArray } = this.props;
    return (
      <Tabs
        activeKey={this.getActiveTabId()}
        onSelect={this.handleTabSelect}
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
}

export { RoutedTabs as _RoutedTabs };
export default withRouter(RoutedTabs);
