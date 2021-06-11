import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import {
  OrganizationsAPI,
  TeamsAPI,
  UsersAPI,
  RolesAPI,
  CredentialsAPI,
} from '../../api';

import ResourceAccessList from './ResourceAccessList';

jest.mock('../../api');

describe('<ResourceAccessList />', () => {
  let wrapper;
  const organization = {
    id: 1,
    name: 'Default',
    summary_fields: {
      object_roles: {
        admin_role: {
          description: 'Can manage all aspects of the organization',
          name: 'Admin',
          id: 2,
          user_only: true,
        },
        execute_role: {
          description: 'May run any executable resources in the organization',
          name: 'Execute',
          id: 3,
        },
        project_admin_role: {
          description: 'Can manage all projects of the organization',
          name: 'Project Admin',
          id: 4,
        },
      },
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

  const history = createMemoryHistory({
    initialEntries: ['/organizations/1/access'],
  });

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
    RolesAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'System Administrator' },
          { id: 14, name: 'System Auditor' },
        ],
      },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList
          resource={organization}
          apiModel={OrganizationsAPI}
        />,
        { context: { router: { history } } }
      );
    });

    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    wrapper.update();
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should fetch and display access records on mount', async () => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalled();
    expect(wrapper.find('ResourceAccessListItem').length).toBe(2);
  });

  test('should open and close confirmation dialog when deleting role', async () => {
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
  });

  test('should delete user role', async () => {
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
  });

  test('should delete team role', async () => {
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
  });

  test('should call api to get org details', async () => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);

    expect(
      wrapper.find('PaginatedTable').prop('toolbarSearchColumns')
    ).toStrictEqual([
      { isDefault: true, key: 'username__icontains', name: 'Username' },
      { key: 'first_name__icontains', name: 'First Name' },
      { key: 'last_name__icontains', name: 'Last Name' },
      {
        key: 'or__roles__in',
        name: 'Roles',
        options: [
          ['2, 1', 'Admin'],
          ['3', 'Execute'],
          ['4', 'Project Admin'],
        ],
      },
    ]);
  });
});

describe('<ResourceAccessList/> for credential access', () => {
  let wrapper;
  const credential = {
    id: 1,
    organization: 20,
    name: 'credential foo bar',
    type: 'credential',
    summary_fields: {
      object_roles: {
        admin_role: {
          description: 'Can manage all aspects of the organization',
          name: 'Admin',
          id: 2,
          user_only: true,
        },
        execute_role: {
          description: 'May run any executable resources in the organization',
          name: 'Execute',
          id: 3,
        },
        project_admin_role: {
          description: 'Can manage all projects of the organization',
          name: 'Project Admin',
          id: 4,
        },
      },
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
                resource_name: 'Cred Foo',
                resource_type: 'credential',
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
                resource_name: 'Cred Bar',
                resource_type: 'credential',
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

  const history = createMemoryHistory({
    initialEntries: ['/credential/1/access'],
  });

  beforeEach(async () => {
    CredentialsAPI.readAccessList.mockResolvedValue({ data });
    CredentialsAPI.readAccessOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    UsersAPI.read.mockResolvedValue({
      data: {
        count: 2,
        results: [
          { id: 1, username: 'foo', url: '' },
          { id: 2, username: 'bar', url: '' },
        ],
      },
    });
    UsersAPI.readOptions.mockResolvedValue({
      data: { related: {}, actions: { GET: {} } },
    });

    TeamsAPI.disassociateRole.mockResolvedValue({});
    UsersAPI.disassociateRole.mockResolvedValue({});
    RolesAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'System Administrator' },
          { id: 14, name: 'System Auditor' },
        ],
      },
    });
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('should render alert of roles not submitted', async () => {
    UsersAPI.readOrganizations.mockResolvedValue({
      data: { count: 2, results: [{ id: 200 }, { id: 250 }] },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList resource={credential} apiModel={CredentialsAPI} />,
        { context: { router: { history } } }
      );
    });

    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    wrapper.update();
    await act(async () => wrapper.find('ToolbarAddButton').prop('onClick')());
    wrapper.update();
    // Step 1
    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(2);
    act(() => wrapper.find('SelectableCard[label="Users"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    // Step 2
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    act(() => wrapper.find('Tr#list-item-14').invoke('onClick')());
    wrapper.update();

    expect(
      wrapper.find('input[aria-label="Select row 1"]').prop('checked')
    ).toBe(true);
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Step 3
    act(() =>
      wrapper.find('Checkbox[aria-label="Admin"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('Checkbox[aria-label="Admin"]').prop('isChecked')).toBe(
      true
    );

    // Save
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    expect(
      wrapper.find('AlertModal[title="Roles not Associated"]')
    ).toHaveLength(1);
    expect(UsersAPI.associateRole).not.toHaveBeenCalled();
  });

  test('should associate role properly, for credential with organization', async () => {
    UsersAPI.readOrganizations.mockResolvedValue({
      data: { count: 2, results: [{ id: 20 }, { id: 250 }] },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList resource={credential} apiModel={CredentialsAPI} />,
        { context: { router: { history } } }
      );
    });
    await act(async () => wrapper.find('ToolbarAddButton').prop('onClick')());
    wrapper.update();
    // Step 1
    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(2);
    act(() => wrapper.find('SelectableCard[label="Users"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    // Step 2
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    act(() => wrapper.find('Tr#list-item-14').invoke('onClick')());
    wrapper.update();
    expect(
      wrapper.find('input[aria-label="Select row 1"]').prop('checked')
    ).toBe(true);
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Step 3
    act(() =>
      wrapper.find('Checkbox[aria-label="Admin"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('Checkbox[aria-label="Admin"]').prop('isChecked')).toBe(
      true
    );

    // Save
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    expect(
      wrapper.find('AlertModal[title="Roles not Associated"]')
    ).toHaveLength(0);
    expect(UsersAPI.associateRole).toHaveBeenCalledWith(14, 2);
  });

  test('should associate role properly, for credential without organization', async () => {
    UsersAPI.readOrganizations.mockResolvedValue({
      data: { count: 2, results: [{ id: 20 }, { id: 250 }] },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList
          resource={{ ...credential, organization: null }}
          apiModel={CredentialsAPI}
        />,
        { context: { router: { history } } }
      );
    });
    await act(async () => wrapper.find('ToolbarAddButton').prop('onClick')());
    wrapper.update();
    // Step 1
    const selectableCardWrapper = wrapper.find('SelectableCard');
    expect(selectableCardWrapper.length).toBe(1);
    act(() => wrapper.find('SelectableCard[label="Users"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    // Step 2
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    act(() => wrapper.find('Tr#list-item-14').invoke('onClick')());

    wrapper.update();
    expect(
      wrapper.find('input[aria-label="Select row 1"]').prop('checked')
    ).toBe(true);
    act(() => wrapper.find('Button[type="submit"]').prop('onClick')());
    wrapper.update();

    // Step 3
    act(() =>
      wrapper.find('Checkbox[aria-label="Admin"]').invoke('onChange')(true)
    );
    wrapper.update();
    expect(wrapper.find('Checkbox[aria-label="Admin"]').prop('isChecked')).toBe(
      true
    );

    // Save
    await act(async () =>
      wrapper.find('Button[type="submit"]').prop('onClick')()
    );
    wrapper.update();

    expect(
      wrapper.find('AlertModal[title="Roles not Associated"]')
    ).toHaveLength(0);
    expect(UsersAPI.associateRole).toHaveBeenCalledWith(14, 2);
  });
});
