import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { OrganizationsAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import OrganizationEdit from './OrganizationEdit';

jest.mock('../../../api');

describe('<OrganizationEdit />', () => {
  const mockData = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    id: 1,
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups',
    },
  };

  test('onSubmit should call api update', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationEdit organization={mockData} />);
    });

    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    wrapper.find('OrganizationForm').prop('onSubmit')(updatedOrgData, [], []);

    expect(OrganizationsAPI.update).toHaveBeenCalledWith(1, updatedOrgData);
  });

  test('onSubmit associates and disassociates instance groups', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationEdit organization={mockData} />);
    });

    const updatedOrgData = {
      name: 'new name',
      description: 'new description',
      custom_virtualenv: 'Buzz',
    };
    await act(async () => {
      wrapper.find('OrganizationForm').invoke('onSubmit')(
        updatedOrgData,
        [3, 4],
        [2]
      );
    });
    expect(OrganizationsAPI.associateInstanceGroup).toHaveBeenCalledWith(1, 3);
    expect(OrganizationsAPI.associateInstanceGroup).toHaveBeenCalledWith(1, 4);
    expect(OrganizationsAPI.disassociateInstanceGroup).toHaveBeenCalledWith(
      1,
      2
    );
  });

  test('should navigate to organization detail when cancel is clicked', async () => {
    const mockInstanceGroups = [
      { name: 'One', id: 1 },
      { name: 'Two', id: 2 },
    ];
    OrganizationsAPI.readInstanceGroups.mockReturnValue({
      data: {
        results: mockInstanceGroups,
      },
    });
    const history = createMemoryHistory({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationEdit organization={mockData} />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/organizations/1/details');
  });
});
