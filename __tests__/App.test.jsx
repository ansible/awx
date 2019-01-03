import React from 'react';
import { HashRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mount, shallow } from 'enzyme';
import { asyncFlush } from '../jest.setup';

import App from '../src/App';

const DEFAULT_ACTIVE_GROUP = 'views_group';

describe('<App />', () => {
  test('expected content is rendered', () => {
    const appWrapper = mount(
      <HashRouter>
        <I18nProvider>
          <App
            routeGroups={[
              {
                groupTitle: 'Group One',
                groupId: 'group_one',
                routes: [
                  { title: 'Foo', path: '/foo' },
                  { title: 'Bar', path: '/bar' },
                ],
              },
              {
                groupTitle: 'Group Two',
                groupId: 'group_two',
                routes: [
                  { title: 'Fiz', path: '/fiz' },
                ]
              }
            ]}
            render={({ routeGroups }) => (
              routeGroups.map(({ groupId }) => (<div key={groupId} id={groupId} />))
            )}
          />
        </I18nProvider>
      </HashRouter>
    );

    // page components
    expect(appWrapper.length).toBe(1);
    expect(appWrapper.find('PageHeader').length).toBe(1);
    expect(appWrapper.find('PageSidebar').length).toBe(1);

    // sidebar groups and route links
    expect(appWrapper.find('NavExpandableGroup').length).toBe(2);
    expect(appWrapper.find('a[href="/#/foo"]').length).toBe(1);
    expect(appWrapper.find('a[href="/#/bar"]').length).toBe(1);
    expect(appWrapper.find('a[href="/#/fiz"]').length).toBe(1);

    // inline render
    expect(appWrapper.find('#group_one').length).toBe(1);
    expect(appWrapper.find('#group_two').length).toBe(1);
  });

  test('onNavToggle sets state.isNavOpen to opposite', () => {
    const appWrapper = shallow(<App />);
    const { onNavToggle } = appWrapper.instance();

    [true, false, true, false, true].forEach(expected => {
      expect(appWrapper.state().isNavOpen).toBe(expected);
      onNavToggle();
    });
  });

  test('onLogoClick sets selected nav back to defaults', () => {
    const appWrapper = shallow(<App />);

    appWrapper.setState({ activeGroup: 'foo', activeItem: 'bar' });
    expect(appWrapper.state().activeItem).toBe('bar');
    expect(appWrapper.state().activeGroup).toBe('foo');

    appWrapper.instance().onLogoClick();
    expect(appWrapper.state().activeGroup).toBe(DEFAULT_ACTIVE_GROUP);
  });

  test('onLogout makes expected call to api client', async (done) => {
    const logout = jest.fn(() => Promise.resolve());
    const api = { logout };

    const appWrapper = shallow(<App api={api} />);

    appWrapper.instance().onLogout();
    await asyncFlush();
    expect(api.logout).toHaveBeenCalledTimes(1);

    done();
  });

  test('Component makes expected call to api client when mounted', () => {
    const getConfig = jest.fn().mockImplementation(() => Promise.resolve({}));
    const api = { getConfig };
    const appWrapper = mount(
      <HashRouter>
        <I18nProvider>
          <App api={api} />
        </I18nProvider>
      </HashRouter>
    );
    expect(getConfig).toHaveBeenCalledTimes(1);
  });
});
