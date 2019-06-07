import React from 'react';

import { mountWithContexts } from '../../../enzymeHelpers';

import OrganizationAdd from '../../../../src/pages/Organizations/screens/OrganizationAdd';
import { OrganizationsAPI } from '../../../../src/api';

jest.mock('../../../../src/api');

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

describe('<OrganizationAdd />', () => {
  let networkProviderValue;

  beforeEach(() => {
    networkProviderValue = {
      handleHttpError: () => {}
    };
  });

  test('handleSubmit should post to api', () => {
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { network: networkProviderValue }
    });
    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    wrapper.find('OrganizationForm').prop('handleSubmit')(updatedOrgData, [], []);
    expect(OrganizationsAPI.create).toHaveBeenCalledWith(updatedOrgData);
  });

  test('should navigate to organizations list when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { router: { history } }
    });
    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(history.push).toHaveBeenCalledWith('/organizations');
  });

  test('should navigate to organizations list when close (x) is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { router: { history } }
    });
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
    OrganizationsAPI.create.mockReturnValueOnce({
      data: {
        id: 5,
        related: {
          instance_groups: '/bar',
        },
        ...orgData,
      }
    });
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { router: { history }, network: networkProviderValue }
    });
    wrapper.find('OrganizationForm').prop('handleSubmit')(orgData, [], []);
    await sleep(0);
    expect(history.push).toHaveBeenCalledWith('/organizations/5');
  });

  test('handleSubmit should post instance groups', async () => {
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { network: networkProviderValue }
    });
    const orgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    OrganizationsAPI.create.mockReturnValueOnce({
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
    expect(OrganizationsAPI.associateInstanceGroup)
      .toHaveBeenCalledWith(5, 3);
  });

  test('AnsibleSelect component renders if there are virtual environments', () => {
    const config = {
      custom_virtualenvs: ['foo', 'bar'],
    };
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { network: networkProviderValue, config }
    }).find('AnsibleSelect');
    expect(wrapper.find('FormSelect')).toHaveLength(1);
    expect(wrapper.find('FormSelectOption')).toHaveLength(2);
  });

  test('AnsibleSelect component does not render if there are 0 virtual environments', () => {
    const config = {
      custom_virtualenvs: [],
    };
    const wrapper = mountWithContexts(<OrganizationAdd />, {
      context: { network: networkProviderValue, config }
    }).find('AnsibleSelect');
    expect(wrapper.find('FormSelect')).toHaveLength(0);
  });
});
