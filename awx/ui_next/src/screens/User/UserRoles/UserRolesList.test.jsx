import React from 'react';
import { act } from 'react-dom/test-utils';
import { UsersAPI, RolesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserRolesList from './UserRolesList';

jest.mock('../../../api/models/Users');
jest.mock('../../../api/models/Roles');

UsersAPI.readOptions.mockResolvedValue({
  data: {
    actions: { GET: {} },
    related_search_fields: [],
  },
});

const user = {
  id: 18,
  username: 'Foo User',
  summary_fields: {
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
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
        name: 'Admin',
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

describe('<UserRolesList />', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('should render properly', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);

    await act(async () => {
      wrapper = mountWithContexts(<UserRolesList user={user} />);
    });

    expect(wrapper.find('UserRolesList').length).toBe(1);
  });

  test('should create proper detailUrl', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);

    await act(async () => {
      wrapper = mountWithContexts(<UserRolesList user={user} />);
    });

    wrapper.update();

    expect(wrapper.find(`Link#userRole-2`).prop('to')).toBe(
      '/templates/job_template/15/details'
    );
    expect(wrapper.find(`Link#userRole-3`).prop('to')).toBe(
      '/templates/workflow_job_template/16/details'
    );
    expect(wrapper.find('Link#userRole-4').prop('to')).toBe(
      '/credentials/75/details'
    );
    expect(wrapper.find('Link#userRole-5').prop('to')).toBe(
      '/inventories/inventory/76/details'
    );
    expect(wrapper.find('Link#userRole-6').prop('to')).toBe(
      '/inventories/smart_inventory/77/details'
    );
  });
  test('should not render add button when user cannot create other users and user cannot edit this user', async () => {
    UsersAPI.readRoleOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [],
      },
    });

    UsersAPI.readRoles.mockResolvedValue({
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
              object_roles: {
                admin_role: {
                  description: 'Can manage all aspects of the job template',
                  name: 'Admin',
                  id: 164,
                },
                execute_role: {
                  description: 'May run the job template',
                  name: 'Execute',
                  id: 165,
                },
                read_role: {
                  description: 'May view settings for the job template',
                  name: 'Read',
                  id: 166,
                },
              },
            },
          },
        ],
        count: 1,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <UserRolesList
          user={{
            ...user,
            summary_fields: {
              user_capabilities: {
                edit: false,
                delete: false,
              },
            },
          }}
        />
      );
    });

    wrapper.update();

    expect(wrapper.find('Button[aria-label="Add resource roles"]').length).toBe(
      0
    );
  });
  test('should open and close wizard', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);
    await act(async () => {
      wrapper = mountWithContexts(<UserRolesList user={user} />);
    });
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[aria-label="Add"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('PFWizard').length).toBe(1);
    await act(async () =>
      wrapper.find("Button[aria-label='Close']").prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('PFWizard').length).toBe(0);
  });
  test('should render disassociate modal', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);

    await act(async () => {
      wrapper = mountWithContexts(<UserRolesList user={user} />);
    });

    wrapper.update();

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
        .find('button[aria-label="Confirm disassociate"]')
        .prop('onClick')()
    );
    expect(RolesAPI.disassociateUserRole).toBeCalledWith(4, 18);
    wrapper.update();
    expect(
      wrapper.find('AlertModal[aria-label="Disassociate role"]').length
    ).toBe(0);
  });
  test('should throw disassociation error', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);
    RolesAPI.disassociateUserRole.mockRejectedValue(
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
      wrapper = mountWithContexts(<UserRolesList user={user} />);
    });

    wrapper.update();

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
        .find('button[aria-label="Confirm disassociate"]')
        .prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('AlertModal[title="Error!"]').length).toBe(1);
  });
  test('user with sys admin privilege should show empty state', async () => {
    UsersAPI.readRoles.mockResolvedValue({
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
      wrapper = mountWithContexts(<UserRolesList user={user} />);
    });

    waitForElement(
      wrapper,
      'EmptyState[title="System Administrator"]',
      el => el.length === 1
    );
  });
});
