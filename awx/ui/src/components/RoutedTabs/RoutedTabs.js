import React from 'react';
import { shape, string, number, arrayOf, node, oneOfType } from 'prop-types';
import { Tab, Tabs, TabTitleText } from '@patternfly/react-core';
import { useHistory, useLocation } from 'react-router-dom';
import styled from 'styled-components';

const Wrapper = styled.div`
  display: flex;
`;

function RoutedTabs({ tabsArray, isWorkflow, children }) {
  const history = useHistory();
  const location = useLocation();

  const getActiveTabId = () => {
    const match = tabsArray.find((tab) => tab.link === location.pathname);
    if (match) {
      return match.id;
    }
    const subpathMatch = tabsArray.find((tab) =>
      location.pathname.startsWith(tab.link)
    );
    if (subpathMatch) {
      return subpathMatch.id;
    }
    return 0;
  };

  const handleTabSelect = (event, eventKey) => {
    const match = tabsArray.find((tab) => tab.id === eventKey);
    if (match) {
      event.preventDefault();
      const link = match.isBackButton
        ? `${match.link}?restoreFilters=true`
        : match.link;
      history.push(link);
    }
  };
  return children ? (
    <Wrapper>
      <Tabs
        activeKey={getActiveTabId()}
        onSelect={handleTabSelect}
        ouiaId="routed-tabs"
      >
        {tabsArray.map((tab) => (
          <Tab
            aria-label={typeof tab.name === 'string' ? tab.name : null}
            eventKey={tab.id}
            key={tab.id}
            href={`#${tab.link}`}
            title={<TabTitleText>{tab.name}</TabTitleText>}
            aria-controls=""
            ouiaId={`${tab.name}-tab`}
          />
        ))}
      </Tabs>
      {children}
    </Wrapper>
  ) : (
    <Tabs
      activeKey={getActiveTabId()}
      onSelect={handleTabSelect}
      ouiaId="routed-tabs"
    >
      {tabsArray.map((tab) => (
        <Tab
          aria-label={typeof tab.name === 'string' ? tab.name : null}
          eventKey={tab.id}
          key={tab.id}
          href={`#${tab.link}`}
          title={<TabTitleText>{tab.name}</TabTitleText>}
          aria-controls=""
          ouiaId={`${tab.name}-tab`}
        />
      ))}
    </Tabs>
  );
}

RoutedTabs.propTypes = {
  tabsArray: arrayOf(
    shape({
      id: number.isRequired,
      link: string.isRequired,
      name: oneOfType([string.isRequired, node.isRequired]),
    })
  ).isRequired,
};

export default RoutedTabs;
