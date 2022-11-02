import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  CredentialsAPI,
  OrganizationsAPI,
  RolesAPI,
  TeamsAPI,
  UsersAPI,
} from 'api';
import { useUserProfile } from 'contexts/Config';
import * as ConfigContext from 'contexts/Config';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

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

  const credentialAccessList = {
    count: 2,
    results: [
      {
        id: 1,
        type: 'user',
        url: '/api/v2/users/1/',
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 20,
                name: 'Admin',
                description: 'Can manage all aspects of the credential',
                resource_name: 'Demo Credential',
                resource_type: 'credential',
                related: { credential: '/api/v2/credentials/1/' },
                user_capabilities: { unattach: false },
              },
              descendant_roles: ['admin_role', 'read_role', 'use_role'],
            },
          ],
          indirect_access: [
            {
              role: {
                id: 1,
                name: 'System Administrator',
                description: 'Can manage all aspects of the system',
                user_capabilities: { unattach: false },
              },
              descendant_roles: ['admin_role', 'read_role', 'use_role'],
            },
          ],
        },
        created: '2022-06-08T18:31:35.834036Z',
        modified: '2022-06-09T16:47:54.712473Z',
        username: 'admin',
        first_name: '',
        last_name: '',
        email: 'admin@localhost',
        is_superuser: true,
        is_system_auditor: false,
        ldap_dn: '',
        last_login: '2022-06-09T16:47:54.712473Z',
        external_account: null,
      },
      {
        id: 2,
        type: 'user',
        url: '/api/v2/users/2/',
        related: {
          teams: '/api/v2/users/2/teams/',
          organizations: '/api/v2/users/2/organizations/',
          admin_of_organizations: '/api/v2/users/2/admin_of_organizations/',
          projects: '/api/v2/users/2/projects/',
          credentials: '/api/v2/users/2/credentials/',
          roles: '/api/v2/users/2/roles/',
          activity_stream: '/api/v2/users/2/activity_stream/',
          access_list: '/api/v2/users/2/access_list/',
          tokens: '/api/v2/users/2/tokens/',
          authorized_tokens: '/api/v2/users/2/authorized_tokens/',
          personal_tokens: '/api/v2/users/2/personal_tokens/',
        },
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 22,
                name: 'Read',
                description: 'May view settings for the credential',
                resource_name: 'Demo Credential',
                resource_type: 'credential',
                related: { credential: '/api/v2/credentials/1/' },
                user_capabilities: { unattach: false },
              },
              descendant_roles: ['read_role'],
            },
          ],
          indirect_access: [],
        },
        created: '2022-06-09T13:45:56.049783Z',
        modified: '2022-06-09T16:48:46.169760Z',
        username: 'second',
        first_name: '',
        last_name: '',
        email: '',
        is_superuser: false,
        is_system_auditor: false,
        ldap_dn: '',
        last_login: '2022-06-09T16:48:46.169760Z',
        external_account: null,
      },
    ],
  };

  const credential = {
    id: 1,
    type: 'credential',
    url: '/api/v2/credentials/1/',
    related: {
      named_url: '/api/v2/credentials/Demo Credential++Machine+ssh++Default/',
      created_by: '/api/v2/users/1/',
      modified_by: '/api/v2/users/1/',
      organization: '/api/v2/organizations/1/',
      activity_stream: '/api/v2/credentials/1/activity_stream/',
      access_list: '/api/v2/credentials/1/access_list/',
      object_roles: '/api/v2/credentials/1/object_roles/',
      owner_users: '/api/v2/credentials/1/owner_users/',
      owner_teams: '/api/v2/credentials/1/owner_teams/',
      copy: '/api/v2/credentials/1/copy/',
      input_sources: '/api/v2/credentials/1/input_sources/',
      credential_type: '/api/v2/credential_types/1/',
    },
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
        description: '',
      },
      credential_type: {
        id: 1,
        name: 'Machine',
        description: '',
      },
      created_by: {
        id: 1,
        username: 'admin',
        first_name: '',
        last_name: '',
      },
      modified_by: {
        id: 1,
        username: 'admin',
        first_name: '',
        last_name: '',
      },
      object_roles: {
        admin_role: {
          description: 'Can manage all aspects of the credential',
          name: 'Admin',
          id: 20,
        },
        use_role: {
          description: 'Can use the credential in a job template',
          name: 'Use',
          id: 21,
        },
        read_role: {
          description: 'May view settings for the credential',
          name: 'Read',
          id: 22,
        },
      },
      user_capabilities: {
        edit: true,
        delete: true,
        copy: false,
        use: true,
      },
      owners: [
        {
          id: 3,
          type: 'user',
          name: 'third',
          description: ' ',
          url: '/api/v2/users/3/',
        },
        {
          id: 1,
          type: 'user',
          name: 'admin',
          description: ' ',
          url: '/api/v2/users/1/',
        },
        {
          id: 1,
          type: 'organization',
          name: 'Default',
          description: '',
          url: '/api/v2/organizations/1/',
        },
      ],
    },
    created: '2022-06-08T18:31:43.491973Z',
    modified: '2022-06-09T19:40:49.460771Z',
    name: 'Demo Credential',
    description: '',
    organization: 1,
    credential_type: 1,
    managed: false,
    inputs: {
      username: 'admin',
      become_method: '',
      become_username: '',
    },
    kind: 'ssh',
    cloud: false,
    kubernetes: false,
  };

  const history = createMemoryHistory({
    initialEntries: ['/organizations/1/access'],
  });

  const credentialHistory = createMemoryHistory({
    initialEntries: ['/credentials/1/access'],
  });

  beforeEach(async () => {
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { id: 2 },
    }));
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: true,
        isSystemAuditor: false,
        isOrgAdmin: false,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
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
    OrganizationsAPI.readAdmins.mockResolvedValue({ data: { count: 1 } });
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
    CredentialsAPI.readAccessList.mockResolvedValue({ credentialAccessList });
    CredentialsAPI.readAccessOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
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

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    wrapper.update();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should fetch and display access records on mount', async () => {
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(OrganizationsAPI.readAccessList).toHaveBeenCalled();
    expect(wrapper.find('ResourceAccessListItem').length).toBe(2);
  });

  test('should open and close confirmation dialog when deleting role', async () => {
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);

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

  test('should show add button for system admin', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList resource={credential} apiModel={CredentialsAPI} />,
        { context: { router: { credentialHistory } } }
      );
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toEqual(1);
  });

  test('should not show add button for non system admin & non org admin', async () => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: false,
        isSystemAuditor: false,
        isOrgAdmin: false,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList resource={credential} apiModel={CredentialsAPI} />,
        { context: { router: { credentialHistory } } }
      );
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toEqual(0);
  });

  test('should show add button for non system admin, org admin, credential admin for credentials associated with org', async () => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: false,
        isSystemAuditor: false,
        isOrgAdmin: true,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList resource={credential} apiModel={CredentialsAPI} />,
        { context: { router: { credentialHistory } } }
      );
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toEqual(1);
  });

  test('should not show add button for non system admin, org admin, credential admin for credentials non associated with org', async () => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: false,
        isSystemAuditor: false,
        isOrgAdmin: true,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ResourceAccessList
          resource={{ ...credential, organization: null }}
          apiModel={CredentialsAPI}
        />,
        { context: { router: { credentialHistory } } }
      );
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toEqual(0);
  });
});
