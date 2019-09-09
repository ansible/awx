import React from 'react';
import { shape, string, number, arrayOf } from 'prop-types';
import { Tab, Tabs as PFTabs } from '@patternfly/react-core';
import { withRouter } from 'react-router-dom';
import styled from 'styled-components';

const Tabs = styled(PFTabs)`
  --pf-c-tabs__button--PaddingLeft: 20px;
  --pf-c-tabs__button--PaddingRight: 20px;

  .pf-c-tabs__list {
    li:first-of-type .pf-c-tabs__button {
      &::before {
        border-left: none;
      }
      &::after {
        margin-left: 0;
      }
    }
  }

  .pf-c-tabs__item.pf-m-current .pf-c-tabs__button {
    font-weight: bold;
  }

  &:not(.pf-c-tabs__item)::before {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    content: '';
    border: solid var(--pf-c-tabs__item--BorderColor);
    border-width: var(--pf-c-tabs__item--BorderWidth) 0
      var(--pf-c-tabs__item--BorderWidth) 0;
  }
`;

function RoutedTabs(props) {
  const { history, tabsArray } = props;

  const getActiveTabId = () => {
    const match = tabsArray.find(tab => tab.link === history.location.pathname);
    if (match) {
      return match.id;
    }
    return 0;
  };

  function handleTabSelect(event, eventKey) {
    const match = tabsArray.find(tab => tab.id === eventKey);
    if (match) {
      history.push(match.link);
    }
  }

  return (
    <Tabs activeKey={getActiveTabId()} onSelect={handleTabSelect}>
      {tabsArray.map(tab => (
        <Tab
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
      pathname: string.isRequired,
    }).isRequired,
  }).isRequired,
  tabsArray: arrayOf(
    shape({
      id: number.isRequired,
      link: string.isRequired,
      name: string.isRequired,
    })
  ).isRequired,
};

export { RoutedTabs as _RoutedTabs };
export default withRouter(RoutedTabs);
