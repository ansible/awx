import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { OrganizationsAPI } from 'api';
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
    id: 1,
    related: {
      instance_groups: '/api/v2/organizations/1/instance_groups',
    },
    default_environment: 1,
    summary_fields: {
      default_environment: {
        id: 1,
        name: 'Baz',
        image: 'quay.io/ansible/awx-ee',
      },
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
      default_environment: null,
    };
    await act(async () => {
      wrapper.find('OrganizationForm').prop('onSubmit')(updatedOrgData, [], []);
    });

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
    };
    const newInstanceGroups = [
      {
        name: 'mock three',
        id: 3,
      },
      {
        name: 'mock four',
        id: 4,
      },
    ];
    const oldInstanceGroups = [
      {
        name: 'mock two',
        id: 2,
      },
    ];

    await act(async () => {
      wrapper.find('OrganizationForm').invoke('onSubmit')(
        updatedOrgData,
        newInstanceGroups,
        oldInstanceGroups
      );
    });
    expect(OrganizationsAPI.orderInstanceGroups).toHaveBeenCalledWith(
      mockData.id,
      newInstanceGroups,
      oldInstanceGroups
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/organizations/1/details');
  });
});
