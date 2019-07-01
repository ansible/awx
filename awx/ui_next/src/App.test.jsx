import React from 'react';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { ConfigAPI, MeAPI, RootAPI } from '@api';
import { asyncFlush } from '../jest.setup';

import App from './App';

jest.mock('./api');

describe('<App />', () => {
  const ansible_version = '111';
  const custom_virtualenvs = [];
  const version = '222';

  beforeEach(() => {
    ConfigAPI.read = () =>
      Promise.resolve({
        data: {
          ansible_version,
          custom_virtualenvs,
          version,
        },
      });
    MeAPI.read = () => Promise.resolve({ data: { results: [{}] } });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

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
            routes: [{ title: 'Fiz', path: '/fiz' }],
          },
        ]}
        render={({ routeGroups }) =>
          routeGroups.map(({ groupId }) => <div key={groupId} id={groupId} />)
        }
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

  test('opening the about modal renders prefetched config data', async done => {
    const wrapper = mountWithContexts(<App />);
    wrapper.update();

    // open about modal
    const aboutDropdown = 'Dropdown QuestionCircleIcon';
    const aboutButton = 'DropdownItem li button';
    const aboutModalContent = 'AboutModalBoxContent';
    const aboutModalClose = 'button[aria-label="Close Dialog"]';

    await waitForElement(wrapper, aboutDropdown);
    wrapper.find(aboutDropdown).simulate('click');

    const button = await waitForElement(
      wrapper,
      aboutButton,
      el => !el.props().disabled
    );
    button.simulate('click');

    // check about modal content
    const content = await waitForElement(wrapper, aboutModalContent);
    expect(content.find('dd').text()).toContain(ansible_version);
    expect(content.find('pre').text()).toContain(`<  AWX ${version}  >`);

    // close about modal
    wrapper.find(aboutModalClose).simulate('click');
    expect(wrapper.find(aboutModalContent)).toHaveLength(0);

    done();
  });

  test('handleNavToggle sets state.isNavOpen to opposite', () => {
    const appWrapper = mountWithContexts(<App />).find('App');

    const { handleNavToggle } = appWrapper.instance();
    [true, false, true, false, true].forEach(expected => {
      expect(appWrapper.state().isNavOpen).toBe(expected);
      handleNavToggle();
    });
  });

  test('onLogout makes expected call to api client', async done => {
    const appWrapper = mountWithContexts(<App />).find('App');
    appWrapper.instance().handleLogout();
    await asyncFlush();
    expect(RootAPI.logout).toHaveBeenCalledTimes(1);
    done();
  });
});
