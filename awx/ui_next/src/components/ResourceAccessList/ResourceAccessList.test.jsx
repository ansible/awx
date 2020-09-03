import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import { OrganizationsAPI, TeamsAPI, UsersAPI } from '../../api';

import ResourceAccessList from './ResourceAccessList';

jest.mock('../../api');

describe('<ResourceAccessList />', () => {
  let wrapper;
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

  beforeEach(async () => {
    OrganizationsAPI.readAccessList.mockResolvedValue({ data });
    OrganizationsAPI.readAccessOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    TeamsAPI.disassociateRole.mockResolvedValue({});
    UsersAPI.disassociateRole.mockResolvedValue({});
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList
          resource={organization}
          apiModel={OrganizationsAPI}
        />
      );
    });
    wrapper.update();
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders succesfully', () => {
    expect(wrapper.find('PaginatedDataList')).toHaveLength(1);
  });

  test('should fetch and display access records on mount', async done => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalled();
    expect(wrapper.find('ResourceAccessListItem').length).toBe(2);
    done();
  });

  test('should open and close confirmation dialog when deleting role', async done => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('DeleteRoleConfirmationModal')).toHaveLength(0);
    const button = wrapper.find('Chip Button').at(0);
    await act(async () => {
      button.prop('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('DeleteRoleConfirmationModal')).toHaveLength(1);
    await act(async () => {
      wrapper.find('DeleteRoleConfirmationModal').prop('onCancel')();
    });
    wrapper.update();
    expect(wrapper.find('DeleteRoleConfirmationModal')).toHaveLength(0);
    expect(TeamsAPI.disassociateRole).not.toHaveBeenCalled();
    expect(UsersAPI.disassociateRole).not.toHaveBeenCalled();
    done();
  });

  it('should delete user role', async done => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const button = wrapper.find('Chip Button').at(0);
    await act(async () => {
      button.prop('onClick')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('DeleteRoleConfirmationModal').prop('onConfirm')();
    });
    wrapper.update();
    expect(wrapper.find('DeleteRoleConfirmationModal')).toHaveLength(0);
    expect(TeamsAPI.disassociateRole).not.toHaveBeenCalled();
    expect(UsersAPI.disassociateRole).toHaveBeenCalledWith(1, 1);
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalledTimes(2);
    done();
  });

  it('should delete team role', async done => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const button = wrapper.find('Chip Button').at(1);
    await act(async () => {
      button.prop('onClick')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('DeleteRoleConfirmationModal').prop('onConfirm')();
    });
    wrapper.update();
    expect(wrapper.find('DeleteRoleConfirmationModal')).toHaveLength(0);
    expect(TeamsAPI.disassociateRole).toHaveBeenCalledWith(5, 3);
    expect(UsersAPI.disassociateRole).not.toHaveBeenCalled();
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalledTimes(2);
    done();
  });
});
