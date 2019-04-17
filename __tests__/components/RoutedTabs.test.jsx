import React from 'react';
import { mount } from 'enzyme';

import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { I18nProvider } from '@lingui/react';
import RoutedTabs from '../../src/components/Tabs/RoutedTabs';

let wrapper;

let history;

beforeEach(() => {
  history = createMemoryHistory({
    initialEntries: ['/organizations/19/details'],
  });
});

const tabs = [
  { name: 'Details', link: 'organizations/19/details', id: 0 },
  { name: 'Access', link: 'organizations/19/access', id: 1 },
  { name: 'Teams', link: 'organizations/19/teams', id: 2 },
  { name: 'Notification', link: 'organizations/19/notification', id: 3 }
];

describe('<RoutedTabs />', () => {
  test('RoutedTabs renders successfully', () => {
    wrapper = mount(
      <I18nProvider>
        <Router history={history}>
          <RoutedTabs
            tabsArray={tabs}
          />
        </Router>
      </I18nProvider>
    ).find('RoutedTabs');
  });

  test('Given a URL the correct tab is displayed', async (done) => {
    wrapper = mount(
      <I18nProvider>
        <Router history={history}>
          <RoutedTabs
            tabsArray={tabs}
          />
        </Router>
      </I18nProvider>
    ).find('RoutedTabs');
    wrapper.find('Tabs').prop('onSelect')({}, 1);
    expect(history.location.pathname).toEqual('/organizations/19/access');
    done();
  });

  test('the correct tab is rendered', async () => {
    wrapper = mount(
      <I18nProvider>
        <Router history={history}>
          <RoutedTabs
            tabsArray={tabs}
          />
        </Router>
      </I18nProvider>
    ).find('RoutedTabs');
    const selectedTab = wrapper.find('section').get(2).props.hidden;
    wrapper.find('button').at(2).simulate('click');
    expect(selectedTab).toBe(false);
  });
});

