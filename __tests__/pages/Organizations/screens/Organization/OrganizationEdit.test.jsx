import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { NetworkProvider } from '../../../../../src/contexts/Network';

import { _OrganizationEdit } from '../../../../../src/pages/Organizations/screens/Organization/OrganizationEdit';

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

describe('<OrganizationEdit />', () => {
  let api;
  let networkProviderValue;

  const mockData = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    id: 1,
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups'
    }
  };

  beforeEach(() => {
    api = {
      getInstanceGroups: jest.fn(),
      updateOrganizationDetails: jest.fn(),
      associateInstanceGroup: jest.fn(),
      disassociate: jest.fn(),
    };

    networkProviderValue = {
      api,
      handleHttpError: () => {}
    };
  });

  test('handleSubmit should call api update', () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <_OrganizationEdit
              organization={mockData}
              api={api}
              handleHttpError={() => {}}
            />
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

    expect(api.updateOrganizationDetails).toHaveBeenCalledWith(
      1,
      updatedOrgData
    );
  });

  test('handleSubmit associates and disassociates instance groups', async () => {
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <_OrganizationEdit
              organization={mockData}
              api={api}
              handleHttpError={() => {}}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    wrapper.find('OrganizationForm').prop('handleSubmit')(updatedOrgData, [3, 4], [2]);
    await sleep(1);

    expect(api.associateInstanceGroup).toHaveBeenCalledWith(
      '/api/v2/organizations/1/instance_groups',
      3
    );
    expect(api.associateInstanceGroup).toHaveBeenCalledWith(
      '/api/v2/organizations/1/instance_groups',
      4
    );
    expect(api.disassociate).toHaveBeenCalledWith(
      '/api/v2/organizations/1/instance_groups',
      2
    );
  });

  test('should navigate to organization detail when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <NetworkProvider value={networkProviderValue}>
            <_OrganizationEdit
              organization={mockData}
              api={api}
              handleHttpError={() => {}}
              history={history}
            />
          </NetworkProvider>
        </I18nProvider>
      </MemoryRouter>
    );

    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();

    expect(history.push).toHaveBeenCalledWith('/organizations/1');
  });
});
