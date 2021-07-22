import React from 'react';
import { act } from 'react-dom/test-utils';
import { MeAPI, RootAPI } from 'api';
import { useAuthorizedPath } from 'contexts/Config';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import AppContainer from './AppContainer';

jest.mock('../../api');
jest.mock('../../util/bootstrapPendo');

global.pendo = {
  initialize: jest.fn(),
};

describe('<AppContainer />', () => {
  const version = '222';

  beforeEach(() => {
    RootAPI.readAssetVariables.mockResolvedValue({
      data: {
        BRAND_NAME: 'AWX',
        PENDO_API_KEY: 'some-pendo-key',
      },
    });
    MeAPI.read.mockResolvedValue({ data: { results: [{}] } });
    useAuthorizedPath.mockImplementation(() => true);
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  test('expected content is rendered', async () => {
    const routeConfig = [
      {
        groupTitle: <span>Group One</span>,
        groupId: 'group_one',
        routes: [
          { title: 'Foo', path: '/foo' },
          { title: 'Bar', path: '/bar' },
        ],
      },
      {
        groupTitle: <span>Group Two</span>,
        groupId: 'group_two',
        routes: [{ title: 'Fiz', path: '/fiz' }],
      },
    ];

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <AppContainer navRouteConfig={routeConfig}>
          {routeConfig.map(({ groupId }) => (
            <div key={groupId} id={groupId} />
          ))}
        </AppContainer>,
        {
          context: {
            config: {
              analytics_status: 'detailed',
              ansible_version: null,
              custom_virtualenvs: [],
              version: '9000',
              me: { is_superuser: true },
              toJSON: () => '/config/',
              license_info: {
                valid_key: true,
              },
            },
          },
        }
      );
    });
    wrapper.update();

    // page components
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('PageHeader').length).toBe(1);
    expect(wrapper.find('PageSidebar').length).toBe(1);

    // sidebar groups and route links
    expect(wrapper.find('NavExpandableGroup').length).toBe(2);
    expect(wrapper.find('a[href="/foo"]').length).toBe(1);
    expect(wrapper.find('a[href="/bar"]').length).toBe(1);
    expect(wrapper.find('a[href="/fiz"]').length).toBe(1);

    expect(wrapper.find('#group_one').length).toBe(1);
    expect(wrapper.find('#group_two').length).toBe(1);

    expect(global.pendo.initialize).toHaveBeenCalledTimes(1);
  });

  test('Pendo not initialized when key is missing', async () => {
    RootAPI.readAssetVariables.mockResolvedValue({
      data: {
        BRAND_NAME: 'AWX',
        PENDO_API_KEY: '',
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AppContainer />, {
        context: {
          config: {
            analytics_status: 'detailed',
            ansible_version: null,
            custom_virtualenvs: [],
            version: '9000',
            me: { is_superuser: true },
            toJSON: () => '/config/',
            license_info: {
              valid_key: true,
            },
          },
        },
      });
    });
    wrapper.update();
    expect(global.pendo.initialize).toHaveBeenCalledTimes(0);
  });

  test('Pendo not initialized when status is analytics off', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AppContainer />, {
        context: {
          config: {
            analytics_status: 'off',
            ansible_version: null,
            custom_virtualenvs: [],
            version: '9000',
            me: { is_superuser: true },
            toJSON: () => '/config/',
            license_info: {
              valid_key: true,
            },
          },
        },
      });
    });
    wrapper.update();
    expect(global.pendo.initialize).toHaveBeenCalledTimes(0);
  });

  test('opening the about modal renders prefetched config data', async () => {
    const aboutDropdown = 'Dropdown QuestionCircleIcon';
    const aboutButton = 'DropdownItem li button';
    const aboutModalContent = 'AboutModalBoxContent';
    const aboutModalClose = 'button[aria-label="Close Dialog"]';

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AppContainer />, {
        context: { config: { version } },
      });
    });

    // open about dropdown menu
    await waitForElement(wrapper, aboutDropdown);
    wrapper.find(aboutDropdown).simulate('click');

    // open about modal
    (
      await waitForElement(wrapper, aboutButton, (el) => !el.props().disabled)
    ).simulate('click');

    // check about modal content
    const content = await waitForElement(wrapper, aboutModalContent);
    expect(content.find('pre').text()).toContain(`<  AWX ${version}  >`);

    // close about modal
    wrapper.find(aboutModalClose).simulate('click');
    expect(wrapper.find(aboutModalContent)).toHaveLength(0);
  });

  test('logout makes expected call to api client', async () => {
    const userMenuButton = 'UserIcon';
    const logoutButton = '#logout-button button';
    const logout = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AppContainer />, {
        context: {
          session: {
            logout,
          },
        },
      });
    });
    // open the user menu
    expect(wrapper.find(logoutButton)).toHaveLength(0);
    wrapper.find(userMenuButton).simulate('click');
    expect(wrapper.find(logoutButton)).toHaveLength(1);

    // logout
    wrapper.find(logoutButton).simulate('click');
    expect(logout).toHaveBeenCalledTimes(1);
  });
});
