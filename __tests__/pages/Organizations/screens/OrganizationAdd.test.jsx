import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { ConfigProvider } from '../../../../src/contexts/Config';
import { NetworkProvider } from '../../../../src/contexts/Network';

import { _OrganizationAdd } from '../../../../src/pages/Organizations/screens/OrganizationAdd';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

describe('<OrganizationAdd />', () => {
  let api;
  let networkProviderValue;

  beforeEach(() => {
    api = {
      getInstanceGroups: jest.fn(),
      createOrganization: jest.fn(),
      associateInstanceGroup: jest.fn(),
      disassociate: jest.fn(),
    };

    networkProviderValue = {
      api,
      handleHttpError: () => {}
    };
  });

  test('handleSubmit should post to api', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider>
              <_OrganizationAdd api={api} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    wrapper.find('OrganizationForm').prop('handleSubmit')(updatedOrgData, [], []);

    expect(api.createOrganization).toHaveBeenCalledWith(updatedOrgData);
  });

  test('should navigate to organizations list when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider>
              <_OrganizationAdd api={api} history={history} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();

    expect(history.push).toHaveBeenCalledWith('/organizations');
  });

  test('should navigate to organizations list when close (x) is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider>
              <_OrganizationAdd api={api} history={history} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Close"]').prop('onClick')();

    expect(history.push).toHaveBeenCalledWith('/organizations');
  });

  test('successful form submission should trigger redirect', async () => {
    const history = {
      push: jest.fn(),
    };
    const orgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    api.createOrganization.mockReturnValueOnce({
      data: {
        id: 5,
        related: {
          instance_groups: '/bar',
        },
        ...orgData,
      }
    });
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider>
              <_OrganizationAdd api={api} history={history} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    wrapper.find('OrganizationForm').prop('handleSubmit')(orgData, [], []);
    await sleep(0);

    expect(history.push).toHaveBeenCalledWith('/organizations/5');
  });

  test('handleSubmit should post instance groups', async () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider>
              <_OrganizationAdd api={api} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    const orgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    api.createOrganization.mockReturnValueOnce({
      data: {
        id: 5,
        related: {
          instance_groups: '/api/v2/organizations/5/instance_groups',
        },
        ...orgData,
      }
    });
    wrapper.find('OrganizationForm').prop('handleSubmit')(orgData, [3], []);
    await sleep(0);

    expect(api.associateInstanceGroup)
      .toHaveBeenCalledWith('/api/v2/organizations/5/instance_groups', 3);
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider value={config}>
              <_OrganizationAdd api={api} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd').find('AnsibleSelect');
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });

  test('AnsibleSelect component does not render if there are 0 virtual environments', () => {
    const config = {
      custom_virtualenvs: [],
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <ConfigProvider value={config}>
              <_OrganizationAdd api={api} />
            </ConfigProvider>
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    ).find('OrganizationAdd').find('AnsibleSelect');
    expect(wrapper.find('FormSelect')).toHaveLength(0);
  });
});
