import React from 'react';
import { mount } from 'enzyme';

import { Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { I18nProvider } from '@lingui/react';
import RoutedTabs from '../../src/components/Tabs/RoutedTabs';
import { DonateIcon } from '@patternfly/react-icons';

let wrapper;

afterEach(() => {
  jest.clearAllMocks();
});
const tabs = [
  { name: 'Details', link: 'organizations/19/details', id: 0 },
  { name: 'Access', link: 'organizations/19/access', id: 1 },
  { name: 'Teams', link: 'organizations/19/teams', id: 2 }
];

const history = createMemoryHistory({
  history: {
    location: {
      pathname: '/organizations/19/details'
    }
  }
});

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

  test('the correct tab is rendered', async () => {
    const currentTab = 'organizations/1/details';
    wrapper = mount(
      <I18nProvider>
        <Router history={history}>
          <RoutedTabs
            tabsArray={tabs}
            location={currentTab}
          />
        </Router>
      </I18nProvider>
    ).find('RoutedTabs');
    wrapper.find('button').at(2).simulate('click');
    wrapper.update();
    expect(history.location.pathname).toEqual('/organizations/19/access');
  });

  test('Given a URL the correct tab is displayed', async (done) => {
    const currentTab = createMemoryHistory({
      initialEntries: ['/organizations/19/teams'],
    });
    wrapper = mount(
      <I18nProvider>
        <Router history={currentTab}>
          <RoutedTabs
            tabsArray={tabs}
          />
        </Router>
      </I18nProvider>
    ).find('RoutedTabs');
    setImmediate(() => {
      wrapper.find('Tabs').prop('onSelect')({}, 2);
      const selectedTab = wrapper.find('li').get(2).props.className;
      expect(selectedTab).toBe('pf-c-tabs__item pf-m-current');
      done();
    });
  });
});
