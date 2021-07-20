import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { CredentialsAPI, OrganizationsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import OrganizationAdd from './OrganizationAdd';

jest.mock('../../../api');

describe('<OrganizationAdd />', () => {
  beforeEach(() => {
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: [
          {
            id: 2,
            type: 'credential',
            name: 'Ansible Galaxy',
            credential_type: 18,
            managed: true,
            kind: 'galaxy_api_token',
          },
        ],
      },
    });
  });

  test('onSubmit should post to api', async () => {
    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      galaxy_credentials: [],
      default_environment: { id: 1, name: 'Foo' },
    };
    OrganizationsAPI.create.mockResolvedValueOnce({ data: {} });
    await act(async () => {
      const wrapper = mountWithContexts(<OrganizationAdd />);
      wrapper.find('OrganizationForm').prop('onSubmit')(updatedOrgData, []);
    });
    expect(OrganizationsAPI.create).toHaveBeenCalledWith({
      ...updatedOrgData,
      default_environment: 1,
    });
    expect(OrganizationsAPI.create).toHaveBeenCalledTimes(1);
  });

  test('should navigate to organizations list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/organizations');
  });

  test('successful form submission should trigger redirect', async () => {
    const history = createMemoryHistory({});
    const orgData = {
      name: 'new name',
      description: 'new description',
      galaxy_credentials: [],
    };
    OrganizationsAPI.create.mockResolvedValueOnce({
      data: {
        id: 5,
        related: {
          instance_groups: '/bar',
        },
        ...orgData,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationAdd />, {
        context: { router: { history } },
      });
      await waitForElement(wrapper, 'button[aria-label="Save"]');
      await wrapper.find('OrganizationForm').prop('onSubmit')(orgData, [3]);
    });
    expect(history.location.pathname).toEqual('/organizations/5');
  });

  test('onSubmit should post instance groups', async () => {
    const orgData = {
      name: 'new name',
      description: 'new description',
      galaxy_credentials: [],
    };
    const mockInstanceGroups = [
      {
        name: 'mock ig',
        id: 3,
      },
    ];
    OrganizationsAPI.create.mockResolvedValueOnce({
      data: {
        id: 5,
        related: {
          instance_groups: '/api/v2/organizations/5/instance_groups',
        },
        ...orgData,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationAdd />);
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await wrapper.find('OrganizationForm').prop('onSubmit')(
      orgData,
      mockInstanceGroups
    );
    expect(OrganizationsAPI.associateInstanceGroup).toHaveBeenCalledWith(5, 3);
  });

  test('onSubmit should post galaxy credentials', async () => {
    const orgData = {
      name: 'new name',
      description: 'new description',
      galaxy_credentials: [
        {
          id: 9000,
        },
      ],
    };
    OrganizationsAPI.create.mockResolvedValueOnce({
      data: {
        id: 5,
        related: {
          instance_groups: '/api/v2/organizations/5/instance_groups',
        },
        ...orgData,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationAdd />);
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await wrapper.find('OrganizationForm').prop('onSubmit')(orgData, [3]);
    expect(OrganizationsAPI.associateGalaxyCredential).toHaveBeenCalledWith(
      5,
      9000
    );
  });

  test('AnsibleSelect component does not render if there are 0 virtual environments', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 },
    ];
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationAdd />, {});
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('AnsibleSelect FormSelect')).toHaveLength(0);
  });
});
