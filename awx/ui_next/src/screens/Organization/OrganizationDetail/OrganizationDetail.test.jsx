import React from 'react';
import { act } from 'react-dom/test-utils';

import { OrganizationsAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import OrganizationDetail from './OrganizationDetail';

jest.mock('../../../api');

describe('<OrganizationDetail />', () => {
  const mockOrganization = {
    name: 'Foo',
    description: 'Bar',
    custom_virtualenv: 'Fizz',
    max_hosts: '0',
    created: '2015-07-07T17:21:26.429745Z',
    modified: '2019-08-11T19:47:37.980466Z',
    summary_fields: {
      user_capabilities: {
        edit: true,
        delete: true,
      },
    },
  };
  const mockInstanceGroups = {
    data: {
      results: [
        { name: 'One', id: 1 },
        { name: 'Two', id: 2 },
      ],
    },
  };

  beforeEach(() => {
    OrganizationsAPI.readInstanceGroups.mockResolvedValue(mockInstanceGroups);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders succesfully', async () => {
    await act(async () => {
      mountWithContexts(<OrganizationDetail organization={mockOrganization} />);
    });
  });

  test('should request instance groups from api', async () => {
    await act(async () => {
      mountWithContexts(<OrganizationDetail organization={mockOrganization} />);
    });
    expect(OrganizationsAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('should render the expected instance group', async () => {
    let component;
    await act(async () => {
      component = mountWithContexts(
        <OrganizationDetail organization={mockOrganization} />
      );
    });
    await waitForElement(component, 'ContentLoading', el => el.length === 0);
    expect(
      component
        .find('Chip')
        .findWhere(el => el.text() === 'One')
        .exists()
    ).toBe(true);
  });

  test('should render Details', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationDetail organization={mockOrganization} />
      );
    });
    const testParams = [
      { label: 'Name', value: 'Foo' },
      { label: 'Description', value: 'Bar' },
      { label: 'Ansible Environment', value: 'Fizz' },
      { label: 'Created', value: '7/7/2015, 5:21:26 PM' },
      { label: 'Last Modified', value: '8/11/2019, 7:47:37 PM' },
      { label: 'Max Hosts', value: '0' },
    ];
    for (let i = 0; i < testParams.length; i++) {
      const { label, value } = testParams[i];
      // eslint-disable-next-line no-await-in-loop
      const detail = await waitForElement(wrapper, `Detail[label="${label}"]`);
      expect(detail.find('dt').text()).toBe(label);
      expect(detail.find('dd').text()).toBe(value);
    }
  });

  test('should show edit button for users with edit permission', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationDetail organization={mockOrganization} />
      );
    });
    const editButton = await waitForElement(
      wrapper,
      'OrganizationDetail Button[aria-label="Edit"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/organizations/undefined/edit');
  });

  test('should hide edit button for users without edit permission', async () => {
    const readOnlyOrg = { ...mockOrganization };
    readOnlyOrg.summary_fields.user_capabilities.edit = false;

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationDetail organization={readOnlyOrg} />
      );
    });
    await waitForElement(wrapper, 'OrganizationDetail');
    expect(
      wrapper.find('OrganizationDetail Button[aria-label="Edit"]').length
    ).toBe(0);
  });

  test('expected api calls are made for delete', async () => {
    OrganizationsAPI.readInstanceGroups.mockResolvedValue({ data: {} });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationDetail organization={mockOrganization} />
      );
    });
    await waitForElement(
      wrapper,
      'OrganizationDetail Button[aria-label="Delete"]'
    );
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(OrganizationsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show content error for failed instance group fetch', async () => {
    OrganizationsAPI.readInstanceGroups.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationDetail organization={mockOrganization} />
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('Error dialog shown for failed deletion', async () => {
    OrganizationsAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationDetail organization={mockOrganization} />
      );
    });
    await waitForElement(
      wrapper,
      'OrganizationDetail Button[aria-label="Delete"]'
    );
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 0
    );
  });
});
