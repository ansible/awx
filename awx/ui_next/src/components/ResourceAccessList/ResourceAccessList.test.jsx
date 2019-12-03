import React from 'react';

import { sleep } from '@testUtils/testUtils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import { OrganizationsAPI, TeamsAPI, UsersAPI } from '@api';

import ResourceAccessList from './ResourceAccessList';

jest.mock('@api');

describe('<ResourceAccessList />', () => {
  const organization = {
    id: 1,
    name: 'Default',
    summary_fields: {
      object_roles: {},
      user_capabilities: {
        edit: true,
      },
    },
  };

  const data = {
    count: 2,
    results: [
      {
        id: 1,
        username: 'joe',
        url: '/foo',
        first_name: 'joe',
        last_name: 'smith',
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 1,
                name: 'Member',
                resource_name: 'Org',
                resource_type: 'organization',
                user_capabilities: { unattach: true },
              },
            },
          ],
          indirect_access: [],
        },
      },
      {
        id: 2,
        username: 'jane',
        url: '/bar',
        first_name: 'jane',
        last_name: 'brown',
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 3,
                name: 'Member',
                resource_name: 'Org',
                resource_type: 'organization',
                team_id: 5,
                team_name: 'The Team',
                user_capabilities: { unattach: true },
              },
            },
          ],
          indirect_access: [],
        },
      },
    ],
  };

  beforeEach(() => {
    OrganizationsAPI.readAccessList.mockResolvedValue({ data });
    TeamsAPI.disassociateRole.mockResolvedValue({});
    UsersAPI.disassociateRole.mockResolvedValue({});
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders succesfully', () => {
    const wrapper = mountWithContexts(
      <ResourceAccessList resource={organization} apiModel={OrganizationsAPI} />
    );
    expect(wrapper.find('PaginatedDataList')).toHaveLength(1);
  });

  test('should fetch and display access records on mount', async done => {
    const wrapper = mountWithContexts(
      <ResourceAccessList resource={organization} apiModel={OrganizationsAPI} />
    );
    await waitForElement(
      wrapper,
      'ResourceAccessListItem',
      el => el.length === 2
    );
    expect(wrapper.find('PaginatedDataList').prop('items')).toEqual(
      data.results
    );
    expect(wrapper.find('ResourceAccessList').state('hasContentLoading')).toBe(
      false
    );
    expect(wrapper.find('ResourceAccessList').state('contentError')).toBe(null);
    done();
  });

  test('should open confirmation dialog when deleting role', async done => {
    const wrapper = mountWithContexts(
      <ResourceAccessList resource={organization} apiModel={OrganizationsAPI} />
    );
    await sleep(0);
    wrapper.update();

    const button = wrapper.find('ChipButton').at(0);
    button.prop('onClick')();
    wrapper.update();

    const component = wrapper.find('ResourceAccessList');
    expect(component.state('deletionRole')).toEqual(
      data.results[0].summary_fields.direct_access[0].role
    );
    expect(component.state('deletionRecord')).toEqual(data.results[0]);
    expect(component.find('DeleteRoleConfirmationModal')).toHaveLength(1);
    done();
  });

  it('should close dialog when cancel button clicked', async done => {
    const wrapper = mountWithContexts(
      <ResourceAccessList resource={organization} apiModel={OrganizationsAPI} />
    );
    await sleep(0);
    wrapper.update();
    const button = wrapper.find('ChipButton').at(0);
    button.prop('onClick')();
    wrapper.update();

    wrapper.find('DeleteRoleConfirmationModal').prop('onCancel')();
    const component = wrapper.find('ResourceAccessList');
    expect(component.state('deletionRole')).toBeNull();
    expect(component.state('deletionRecord')).toBeNull();
    expect(TeamsAPI.disassociateRole).not.toHaveBeenCalled();
    expect(UsersAPI.disassociateRole).not.toHaveBeenCalled();
    done();
  });

  it('should delete user role', async done => {
    const wrapper = mountWithContexts(
      <ResourceAccessList resource={organization} apiModel={OrganizationsAPI} />
    );
    const button = await waitForElement(
      wrapper,
      'ChipButton',
      el => el.length === 2
    );
    button.at(0).prop('onClick')();

    const confirmation = await waitForElement(
      wrapper,
      'DeleteRoleConfirmationModal'
    );
    confirmation.prop('onConfirm')();
    await waitForElement(
      wrapper,
      'DeleteRoleConfirmationModal',
      el => el.length === 0
    );

    await sleep(0);
    wrapper.update();
    const component = wrapper.find('ResourceAccessList');
    expect(component.state('deletionRole')).toBeNull();
    expect(component.state('deletionRecord')).toBeNull();
    expect(TeamsAPI.disassociateRole).not.toHaveBeenCalled();
    expect(UsersAPI.disassociateRole).toHaveBeenCalledWith(1, 1);
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalledTimes(2);
    done();
  });

  it('should delete team role', async done => {
    const wrapper = mountWithContexts(
      <ResourceAccessList resource={organization} apiModel={OrganizationsAPI} />
    );
    const button = await waitForElement(
      wrapper,
      'ChipButton',
      el => el.length === 2
    );
    button.at(1).prop('onClick')();

    const confirmation = await waitForElement(
      wrapper,
      'DeleteRoleConfirmationModal'
    );
    confirmation.prop('onConfirm')();
    await waitForElement(
      wrapper,
      'DeleteRoleConfirmationModal',
      el => el.length === 0
    );

    await sleep(0);
    wrapper.update();
    const component = wrapper.find('ResourceAccessList');
    expect(component.state('deletionRole')).toBeNull();
    expect(component.state('deletionRecord')).toBeNull();
    expect(TeamsAPI.disassociateRole).toHaveBeenCalledWith(5, 3);
    expect(UsersAPI.disassociateRole).not.toHaveBeenCalled();
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalledTimes(2);
    done();
  });
});
