import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mount, shallow } from 'enzyme';
import { asyncFlush } from '../jest.setup';

import App from '../src/App';

describe('<App />', () => {
  test('expected content is rendered', () => {
    const appWrapper = mount(
      <MemoryRouter>
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
      </MemoryRouter>
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

    const getConfig = jest.fn(() => Promise.resolve({ data: { ansible_version, version } }));
    const api = { getConfig };

    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <App api={api} />
        </I18nProvider>
      </MemoryRouter>
    );

    await asyncFlush();
    expect(getConfig).toHaveBeenCalledTimes(1);

    // open about modal
    const aboutDropdown = 'Dropdown QuestionCircleIcon';
    const aboutButton = 'DropdownItem li button';
    const aboutModalContent = 'AboutModalBoxContent';
    const aboutModalClose = 'button[aria-label="Close Dialog"]';

    expect(wrapper.find(aboutModalContent)).toHaveLength(0);
    wrapper.find(aboutDropdown).simulate('click');
    wrapper.find(aboutButton).simulate('click');
    wrapper.update();

    // check about modal content
    const content = wrapper.find(aboutModalContent);
    expect(content).toHaveLength(1);
    expect(content.find('dd').text()).toContain(ansible_version);
    expect(content.find('pre').text()).toContain(`<  Tower ${version}  >`);

    // close about modal
    wrapper.find(aboutModalClose).simulate('click');
    expect(wrapper.find(aboutModalContent)).toHaveLength(0);

    done();
  });

  test('onNavToggle sets state.isNavOpen to opposite', () => {
    const appWrapper = shallow(<App />);
    const { onNavToggle } = appWrapper.instance();

    [true, false, true, false, true].forEach(expected => {
      expect(appWrapper.state().isNavOpen).toBe(expected);
      onNavToggle();
    });
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
});
