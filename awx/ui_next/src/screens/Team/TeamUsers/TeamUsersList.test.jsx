import React from 'react';
import { act } from 'react-dom/test-utils';
import { TeamsAPI, UsersAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import TeamUsersList from './TeamUsersList';

jest.mock('../../../api/models/Teams');
jest.mock('../../../api/models/Users');

const teamUsersList = {
  data: {
    count: 3,
    results: [
      {
        id: 1,
        type: 'user',
        url: '',
        summary_fields: {
          direct_access: [],
          indirect_access: [
            {
              role: {
                id: 1,
              },
            },
          ],
        },
        created: '2020-06-19T12:55:13.138692Z',
        username: 'admin',
        first_name: '',
        last_name: '',
        email: 'a@g.com',
      },
      {
        id: 5,
        type: 'user',
        url: '',
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 40,
                name: 'Member',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['member_role', 'read_role'],
            },
            {
              role: {
                id: 41,
                name: 'Read',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['member_role', 'read_role'],
            },
          ],
          indirect_access: [],
        },
        created: '2020-06-19T13:01:44.183577Z',
        username: 'jt_admin',
        first_name: '',
        last_name: '',
        email: '',
      },
      {
        id: 2,
        type: 'user',
        url: '',
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 40,
                name: 'Alex',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['member_role', 'read_role'],
            },
            {
              role: {
                id: 41,
                name: 'Read',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['member_role', 'read_role'],
            },
          ],
          indirect_access: [
            {
              role: {
                id: 2,
                name: 'Admin',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['admin_role', 'member_role', 'read_role'],
            },
          ],
        },
        created: '2020-06-19T13:01:43.674349Z',
        username: 'org_admin',
        first_name: '',
        last_name: '',
        email: '',
      },
      {
        id: 3,
        type: 'user',
        url: '',
        summary_fields: {
          direct_access: [
            {
              role: {
                id: 40,
                name: 'Savannah',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['member_role', 'read_role'],
            },
            {
              role: {
                id: 41,
                name: 'Read',
                user_capabilities: {
                  unattach: true,
                },
              },
              descendant_roles: ['member_role', 'read_role'],
            },
          ],
          indirect_access: [],
        },
        created: '2020-06-19T13:01:43.868499Z',
        username: 'org_member',
        first_name: '',
        last_name: '',
        email: '',
      },
    ],
  },
};

describe('<TeamUsersList />', () => {
  let wrapper;

  beforeEach(() => {
    TeamsAPI.readUsersAccess = jest.fn(() =>
      Promise.resolve({
        data: teamUsersList.data,
      })
    );
    TeamsAPI.readUsersAccessOptions = jest.fn(() =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      })
    );
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should load and render users', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<TeamUsersList />);
    });
    wrapper.update();

    expect(wrapper.find('TeamUserListItem')).toHaveLength(4);
  });

  test('should disassociate role', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<TeamUsersList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('Label[aria-label="Member"]').prop('onClose')({
        id: 1,
        name: 'Member',
      });
    });
    wrapper.update();
    expect(wrapper.find('AlertModal[title="Disassociate roles"]').length).toBe(
      1
    );
    await act(async () => {
      wrapper
        .find('Button[aria-label="confirm disassociation"]')
        .prop('onClick')();
    });

    expect(UsersAPI.disassociateRole).toHaveBeenCalledTimes(1);
    expect(TeamsAPI.readUsersAccess).toHaveBeenCalledTimes(2);
  });

  test('should show disassociation error', async () => {
    UsersAPI.disassociateRole.mockResolvedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/users/1',
          },
          data: 'An error occurred',
        },
      })
    );

    await act(async () => {
      wrapper = mountWithContexts(<TeamUsersList />);
    });
    waitForElement(wrapper, 'ContentLoading', el => el.length === 0);

    await act(async () => {
      wrapper.find('Label[aria-label="Member"]').prop('onClose')({
        id: 1,
        name: 'Member',
      });
    });

    wrapper.update();
    expect(wrapper.find('AlertModal[title="Disassociate roles"]').length).toBe(
      1
    );

    await act(async () => {
      wrapper
        .find('Button[aria-label="confirm disassociation"]')
        .prop('onClick')();
    });

    wrapper.update();
    expect(UsersAPI.disassociateRole).toHaveBeenCalled();

    const modal = wrapper.find('Modal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });
});
