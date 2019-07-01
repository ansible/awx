/* eslint-disable react/jsx-pascal-case */
import React from 'react';
import { mount, shallow } from 'enzyme';
import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { Tab } from '@patternfly/react-core';
import RoutedTabs, { _RoutedTabs } from './RoutedTabs';

let wrapper;
let history;

const tabs = [
  { name: 'Details', link: '/organizations/19/details', id: 1 },
  { name: 'Access', link: '/organizations/19/access', id: 2 },
  { name: 'Teams', link: '/organizations/19/teams', id: 3 },
  { name: 'Notification', link: '/organizations/19/notification', id: 4 },
];

describe('<RoutedTabs />', () => {
  beforeEach(() => {
    history = createMemoryHistory({
      initialEntries: ['/organizations/19/teams'],
    });
  });

  test('RoutedTabs renders successfully', () => {
    wrapper = shallow(<_RoutedTabs tabsArray={tabs} history={history} />);
    expect(wrapper.find(Tab)).toHaveLength(4);
  });

  test('Given a URL the correct tab is active', async () => {
    wrapper = mount(
      <Router history={history}>
        <RoutedTabs tabsArray={tabs} />
      </Router>
    );

    expect(history.location.pathname).toEqual('/organizations/19/teams');
    expect(wrapper.find('Tabs').prop('activeKey')).toBe(3);
  });

  test('should update history when new tab selected', async () => {
    wrapper = mount(
      <Router history={history}>
        <RoutedTabs tabsArray={tabs} />
      </Router>
    );

    wrapper.find('Tabs').prop('onSelect')({}, 2);
    wrapper.update();

    expect(history.location.pathname).toEqual('/organizations/19/access');
    expect(wrapper.find('Tabs').prop('activeKey')).toBe(2);
  });
});
