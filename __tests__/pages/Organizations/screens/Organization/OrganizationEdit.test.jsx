import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';

import OrganizationEdit from '../../../../../src/pages/Organizations/screens/Organization/OrganizationEdit';

import { OrganizationsAPI } from '../../../../../src/api';

jest.mock('../../../../../src/api');

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

describe('<OrganizationEdit />', () => {
  let api;

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
  });

  test('handleSubmit should call api update', () => {
    const wrapper = mountWithContexts(
      <OrganizationEdit
        organization={mockData}
      />, { context: { network: {
        api,
        handleHttpError: () => {}
      } } }
    );

    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    wrapper.find('OrganizationForm').prop('handleSubmit')(updatedOrgData, [], []);

    expect(OrganizationsAPI.update).toHaveBeenCalledWith(1, updatedOrgData);
  });

  test('handleSubmit associates and disassociates instance groups', async () => {
    const wrapper = mountWithContexts(
      <OrganizationEdit
        organization={mockData}
      />, { context: { network: {
        api,
        handleHttpError: () => {}
      } } }
    );

    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    wrapper.find('OrganizationForm').prop('handleSubmit')(updatedOrgData, [3, 4], [2]);
    await sleep(1);

    expect(OrganizationsAPI.associateInstanceGroup).toHaveBeenCalledWith(1, 3);
    expect(OrganizationsAPI.associateInstanceGroup).toHaveBeenCalledWith(1, 4);
    expect(OrganizationsAPI.disassociateInstanceGroup).toHaveBeenCalledWith(1, 2);
  });

  test('should navigate to organization detail when cancel is clicked', () => {
    const history = {
      push: jest.fn(),
    };
    const wrapper = mountWithContexts(
      <OrganizationEdit
        organization={mockData}
      />, { context: {
        network: {
          api: { api },
          handleHttpError: () => {}
        },
        router: { history }
      } }
    );

    expect(history.push).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();

    expect(history.push).toHaveBeenCalledWith('/organizations/1');
  });
});
