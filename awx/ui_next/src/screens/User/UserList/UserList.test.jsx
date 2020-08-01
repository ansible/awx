import React from 'react';
import { act } from 'react-dom/test-utils';
import { UsersAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import UsersList from './UserList';

jest.mock('../../../api');

let wrapper;
const mockUsers = [
  {
    id: 1,
    type: 'user',
    url: '/api/v2/users/1/',
    related: {
      teams: '/api/v2/users/1/teams/',
      organizations: '/api/v2/users/1/organizations/',
      admin_of_organizations: '/api/v2/users/1/admin_of_organizations/',
      projects: '/api/v2/users/1/projects/',
      credentials: '/api/v2/users/1/credentials/',
      roles: '/api/v2/users/1/roles/',
      activity_stream: '/api/v2/users/1/activity_stream/',
      access_list: '/api/v2/users/1/access_list/',
      tokens: '/api/v2/users/1/tokens/',
      authorized_tokens: '/api/v2/users/1/authorized_tokens/',
      personal_tokens: '/api/v2/users/1/personal_tokens/',
    },
    summary_fields: {
      user_capabilities: {
        edit: true,
        delete: true,
      },
    },
    created: '2019-10-28T15:01:07.218634Z',
    username: 'admin',
    first_name: 'Admin',
    last_name: 'User',
    email: 'admin@ansible.com',
    is_superuser: true,
    is_system_auditor: false,
    ldap_dn: '',
    last_login: '2019-11-05T18:12:57.367622Z',
    external_account: null,
    auth: [],
  },
  {
    id: 9,
    type: 'user',
    url: '/api/v2/users/9/',
    related: {
      teams: '/api/v2/users/9/teams/',
      organizations: '/api/v2/users/9/organizations/',
      admin_of_organizations: '/api/v2/users/9/admin_of_organizations/',
      projects: '/api/v2/users/9/projects/',
      credentials: '/api/v2/users/9/credentials/',
      roles: '/api/v2/users/9/roles/',
      activity_stream: '/api/v2/users/9/activity_stream/',
      access_list: '/api/v2/users/9/access_list/',
      tokens: '/api/v2/users/9/tokens/',
      authorized_tokens: '/api/v2/users/9/authorized_tokens/',
      personal_tokens: '/api/v2/users/9/personal_tokens/',
    },
    summary_fields: {
      user_capabilities: {
        edit: true,
        delete: false,
      },
    },
    created: '2019-11-04T18:52:13.565525Z',
    username: 'systemauditor',
    first_name: 'System',
    last_name: 'Auditor',
    email: 'systemauditor@ansible.com',
    is_superuser: false,
    is_system_auditor: true,
    ldap_dn: '',
    last_login: null,
    external_account: null,
    auth: [],
  },
];

beforeEach(() => {
  UsersAPI.destroy = jest.fn();
  UsersAPI.read.mockResolvedValue({
    data: {
      count: mockUsers.length,
      results: mockUsers,
    },
  });
});

afterEach(() => {
  jest.clearAllMocks();
  wrapper.unmount();
});

describe('UsersList with full permissions', () => {
  beforeAll(() => {
    UsersAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
  });

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UsersList />);
    });
    wrapper.update();
  });

  test('Users are retrieved from the api and the components finishes loading', async () => {
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(UsersAPI.read).toHaveBeenCalled();
  });

  test('should show add button', () => {
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('DataListCheck[id="select-user-1"]').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-user-1"]').invoke('onChange')(
        true
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-user-1"]').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-user-1"]').invoke('onChange')(
        false
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-user-1"]').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
  });

  test('should call api delete users for each selected user', async () => {
    await act(async () => {
      wrapper.find('DataListCheck[id="select-user-1"]').invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();
    expect(UsersAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show error modal when user is not successfully deleted from api', async () => {
    UsersAPI.destroy.mockImplementationOnce(() => Promise.reject(new Error()));
    // expect(wrapper.debug()).toBe(false);
    expect(wrapper.find('Modal').length).toBe(0);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-user-1"]').invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(1);
    await act(async () => {
      wrapper.find('ModalBoxCloseButton').invoke('onClose')();
    });
    wrapper.update();
    expect(wrapper.find('Modal').length).toBe(0);
  });
});

describe('UsersList without full permissions', () => {
  test('Add button hidden for users without ability to POST', async () => {
    UsersAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });

    await act(async () => {
      wrapper = mountWithContexts(<UsersList />);
    });
    wrapper.update();
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});

describe('read call unsuccessful', () => {
  test('should show content error when read call unsuccessful', async () => {
    UsersAPI.read.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(<UsersList />);
    });
    wrapper.update();
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
