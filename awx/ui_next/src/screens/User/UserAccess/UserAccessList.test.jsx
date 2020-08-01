import React from 'react';
import { act } from 'react-dom/test-utils';
import { UsersAPI, RolesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserAccessList from './UserAccessList';

jest.mock('../../../api/models/Users');
jest.mock('../../../api/models/Roles');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 18,
  }),
}));
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
const options = {
  data: { actions: { POST: { id: 1, disassociate: true } } },
};
describe('<UserAccessList />', () => {
  let wrapper;
  afterEach(() => {
    jest.clearAllMocks();
    // wrapper.unmount();
  });
  test('should render properly', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);
    UsersAPI.readRoleOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<UserAccessList />);
    });

    expect(wrapper.find('UserAccessList').length).toBe(1);
  });

  test('should create proper detailUrl', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);
    UsersAPI.readRoleOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<UserAccessList />);
    });

    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);

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
  test('should not render add button', async () => {
    UsersAPI.readRoleOptions.mockResolvedValueOnce({
      data: {},
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
      wrapper = mountWithContexts(<UserAccessList />);
    });

    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Add resource roles"]').length).toBe(
      0
    );
  });
  test('should open and close wizard', async () => {
    UsersAPI.readRoles.mockResolvedValue(roles);
    UsersAPI.readRoleOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<UserAccessList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);
    await act(async () =>
      wrapper.find('Button[aria-label="Add resource roles"]').prop('onClick')()
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
    UsersAPI.readRoleOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<UserAccessList />);
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
    UsersAPI.readRoleOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<UserAccessList />);
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
    UsersAPI.readRoleOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<UserAccessList />);
    });

    waitForElement(
      wrapper,
      'EmptyState[title="System Administrator"]',
      el => el.length === 1
    );
  });
});
