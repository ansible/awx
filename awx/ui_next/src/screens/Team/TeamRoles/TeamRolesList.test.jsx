import React from 'react';
import { act } from 'react-dom/test-utils';
import { TeamsAPI, RolesAPI, UsersAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import TeamRolesList from './TeamRolesList';

jest.mock('../../../api/models/Teams');
jest.mock('../../../api/models/Roles');
jest.mock('../../../api/models/Users');

const me = {
  id: 1,
};

const team = {
  id: 18,
  type: 'team',
  url: '/api/v2/teams/1/',
  related: {
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    projects: '/api/v2/teams/1/projects/',
    users: '/api/v2/teams/1/users/',
    credentials: '/api/v2/teams/1/credentials/',
    roles: '/api/v2/teams/1/roles/',
    object_roles: '/api/v2/teams/1/object_roles/',
    activity_stream: '/api/v2/teams/1/activity_stream/',
    access_list: '/api/v2/teams/1/access_list/',
    organization: '/api/v2/organizations/1/',
  },
  summary_fields: {
    organization: {
      id: 1,
      name: 'Default',
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
        description: 'Can manage all aspects of the team',
        name: 'Admin',
        id: 33,
      },
      member_role: {
        description: 'User is a member of the team',
        name: 'Member',
        id: 34,
      },
      read_role: {
        description: 'May view settings for the team',
        name: 'Read',
        id: 35,
      },
    },
    user_capabilities: {
      edit: false,
      delete: false,
    },
  },
  created: '2020-07-22T18:21:54.233411Z',
  modified: '2020-07-22T18:21:54.233442Z',
  name: 'a team',
  description: '',
  organization: 1,
};

const roles = {
  data: {
    results: [
      {
        id: 2,
        name: 'Admin',
        type: 'role',
        url: '/api/v2/roles/257/',
        summary_fields: {
          resource_name: 'template delete project',
          resource_id: 15,
          resource_type: 'job_template',
          resource_type_display_name: 'Job Template',
          user_capabilities: { unattach: true },
        },
      },
      {
        id: 3,
        name: 'Admin Read Only',
        type: 'role',
        url: '/api/v2/roles/257/',
        summary_fields: {
          resource_name: 'template delete project',
          resource_id: 16,
          resource_type: 'workflow_job_template',
          resource_type_display_name: 'Job Template',
          user_capabilities: { unattach: true },
        },
      },
      {
        id: 4,
        name: 'Execute',
        type: 'role',
        url: '/api/v2/roles/258/',
        summary_fields: {
          resource_name: 'Credential Bar',
          resource_id: 75,
          resource_type: 'credential',
          resource_type_display_name: 'Credential',
          user_capabilities: { unattach: true },
        },
      },
      {
        id: 5,
        name: 'Update',
        type: 'role',
        url: '/api/v2/roles/259/',
        summary_fields: {
          resource_name: 'Inventory Foo',
          resource_id: 76,
          resource_type: 'inventory',
          resource_type_display_name: 'Inventory',
          user_capabilities: { unattach: true },
        },
      },
      {
        id: 6,
        name: 'Admin',
        type: 'role',
        url: '/api/v2/roles/260/',
        summary_fields: {
          resource_name: 'Smart Inventory Foo',
          resource_id: 77,
          resource_type: 'smart_inventory',
          resource_type_display_name: 'Inventory',
          user_capabilities: { unattach: true },
        },
      },
    ],
    count: 5,
  },
};

describe('<TeamRolesList />', () => {
  let wrapper;

  beforeEach(() => {
    UsersAPI.readAdminOfOrganizations.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 1,
          name: 'Foo Org',
        },
      ],
    });

    TeamsAPI.readRoleOptions.mockResolvedValue({
      data: {
        actions: { GET: {} },
        related_search_fields: [],
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('should render properly', async () => {
    TeamsAPI.readRoles.mockResolvedValue(roles);

    await act(async () => {
      wrapper = mountWithContexts(<TeamRolesList me={me} team={team} />);
    });
    expect(wrapper.find('TeamRolesList').length).toBe(1);
  });

  test('should create proper detailUrl', async () => {
    TeamsAPI.readRoles.mockResolvedValue(roles);

    await act(async () => {
      wrapper = mountWithContexts(<TeamRolesList me={me} team={team} />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);

    expect(wrapper.find(`Link#teamRole-2`).prop('to')).toBe(
      '/templates/job_template/15/details'
    );
    expect(wrapper.find(`Link#teamRole-3`).prop('to')).toBe(
      '/templates/workflow_job_template/16/details'
    );
    expect(wrapper.find('Link#teamRole-4').prop('to')).toBe(
      '/credentials/75/details'
    );
    expect(wrapper.find('Link#teamRole-5').prop('to')).toBe(
      '/inventories/inventory/76/details'
    );
    expect(wrapper.find('Link#teamRole-6').prop('to')).toBe(
      '/inventories/smart_inventory/77/details'
    );
  });
  test('should not render add button when user cannot edit team and is not an admin of the org', async () => {
    UsersAPI.readAdminOfOrganizations.mockResolvedValueOnce({
      count: 0,
      results: [],
    });

    TeamsAPI.readRoles.mockResolvedValue({
      data: {
        results: [
          {
            id: 2,
            name: 'Admin',
            type: 'role',
            url: '/api/v2/roles/257/',
            summary_fields: {
              resource_name: 'template delete project',
              resource_id: 15,
              resource_type: 'job_template',
              resource_type_display_name: 'Job Template',
              user_capabilities: { unattach: true },
            },
            description: 'Can manage all aspects of the job template',
          },
        ],
        count: 1,
      },
    });

    await act(async () => {
      wrapper = mountWithContexts(<TeamRolesList me={me} team={team} />);
    });

    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Add resource roles"]').length).toBe(
      0
    );
  });

  test('should render disassociate modal', async () => {
    TeamsAPI.readRoles.mockResolvedValue(roles);

    await act(async () => {
      wrapper = mountWithContexts(<TeamRolesList me={me} team={team} />);
    });

    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);

    await act(async () =>
      wrapper.find('Chip[aria-label="Execute"]').prop('onClick')({
        id: 4,
        name: 'Execute',
        type: 'role',
        url: '/api/v2/roles/258/',
        summary_fields: {
          resource_name: 'Credential Bar',
          resource_id: 75,
          resource_type: 'credential',
          resource_type_display_name: 'Credential',
          user_capabilities: { unattach: true },
        },
      })
    );
    wrapper.update();
    expect(
      wrapper.find('AlertModal[aria-label="Disassociate role"]').length
    ).toBe(1);
    await act(async () =>
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .prop('onClick')()
    );
    expect(RolesAPI.disassociateTeamRole).toBeCalledWith(4, 18);
    wrapper.update();
    expect(
      wrapper.find('AlertModal[aria-label="Disassociate role"]').length
    ).toBe(0);
  });

  test('should throw disassociation error', async () => {
    TeamsAPI.readRoles.mockResolvedValue(roles);
    RolesAPI.disassociateTeamRole.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/roles/18/roles',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await act(async () => {
      wrapper = mountWithContexts(<TeamRolesList me={me} team={team} />);
    });

    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);

    await act(async () =>
      wrapper.find('Chip[aria-label="Execute"]').prop('onClick')({
        id: 4,
        name: 'Execute',
        type: 'role',
        url: '/api/v2/roles/258/',
        summary_fields: {
          resource_name: 'Credential Bar',
          resource_id: 75,
          resource_type: 'credential',
          resource_type_display_name: 'Credential',
          user_capabilities: { unattach: true },
        },
      })
    );
    wrapper.update();
    expect(
      wrapper.find('AlertModal[aria-label="Disassociate role"]').length
    ).toBe(1);
    await act(async () =>
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('AlertModal[title="Error!"]').length).toBe(1);
  });

  test('user with sys admin privilege should show empty state', async () => {
    TeamsAPI.readRoles.mockResolvedValue({
      data: {
        results: [
          {
            id: 2,
            name: 'System Administrator',
            type: 'role',
            url: '/api/v2/roles/257/',
            summary_fields: {
              resource_name: 'template delete project',
              resource_id: 15,
              resource_type: 'job_template',
              resource_type_display_name: 'Job Template',
              user_capabilities: { unattach: true },
            },
          },
        ],
        count: 1,
      },
    });

    await act(async () => {
      wrapper = mountWithContexts(<TeamRolesList me={me} team={team} />);
    });

    waitForElement(
      wrapper,
      'EmptyState[title="System Administrator"]',
      el => el.length === 1
    );
  });
});
