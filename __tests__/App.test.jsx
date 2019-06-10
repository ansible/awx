import React from 'react';

import { mountWithContexts, waitForElement } from './enzymeHelpers';

import { asyncFlush } from '../jest.setup';

import App from '../src/App';

import { RootAPI } from '../src/api';

jest.mock('../src/api');

describe('<App />', () => {
  test('expected content is rendered', () => {
    const appWrapper = mountWithContexts(
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

  test('opening the about modal renders prefetched config data', async (done) => {
    const ansible_version = '111';
    const version = '222';

    const config = { ansible_version, version };

    const wrapper = mountWithContexts(<App />, { context: { config } });

    // open about modal
    const aboutDropdown = 'Dropdown QuestionCircleIcon';
    const aboutButton = 'DropdownItem li button';
    const aboutModalContent = 'AboutModalBoxContent';
    const aboutModalClose = 'button[aria-label="Close Dialog"]';

    expect(wrapper.find(aboutModalContent)).toHaveLength(0);
    wrapper.find(aboutDropdown).simulate('click');
    wrapper.find(aboutButton).simulate('click');

    // check about modal content
    const content = await waitForElement(wrapper, aboutModalContent);
    expect(content.find('dd').text()).toContain(ansible_version);
    expect(content.find('pre').text()).toContain(`<  AWX ${version}  >`);

    // close about modal
    wrapper.find(aboutModalClose).simulate('click');
    expect(wrapper.find(aboutModalContent)).toHaveLength(0);

    done();
  });

  test('onNavToggle sets state.isNavOpen to opposite', () => {
    const appWrapper = mountWithContexts(<App />).find('App');
    const { onNavToggle } = appWrapper.instance();
    [true, false, true, false, true].forEach(expected => {
      expect(appWrapper.state().isNavOpen).toBe(expected);
      onNavToggle();
    });
  });

  test('onLogout makes expected call to api client', async (done) => {
    const appWrapper = mountWithContexts(<App />, {
      context: { network: { handleHttpError: () => {} } }
    }).find('App');

    appWrapper.instance().onLogout();
    await asyncFlush();
    expect(RootAPI.logout).toHaveBeenCalledTimes(1);

    done();
  });
});
