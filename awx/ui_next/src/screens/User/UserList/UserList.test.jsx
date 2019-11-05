import React from 'react';
import { UsersAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import UsersList, { _UsersList } from './UserList';

jest.mock('@api');

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

describe('<UsersList />', () => {
  beforeEach(() => {
    UsersAPI.read.mockResolvedValue({
      data: {
        count: mockUsers.length,
        results: mockUsers,
      },
    });

    UsersAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <UsersList
        match={{ path: '/users', url: '/users' }}
        location={{ search: '', pathname: '/users' }}
      />
    );
  });

  test('Users are retrieved from the api and the components finishes loading', async done => {
    const loadUsers = jest.spyOn(_UsersList.prototype, 'loadUsers');
    const wrapper = mountWithContexts(<UsersList />);
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === true
    );
    expect(loadUsers).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === false
    );
    done();
  });

  test('handleSelect is called when a user list item is selected', async done => {
    const handleSelect = jest.spyOn(_UsersList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<UsersList />);
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === false
    );
    await wrapper
      .find('input#select-user-1')
      .closest('DataListCheck')
      .props()
      .onChange();
    expect(handleSelect).toBeCalled();
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('selected').length === 1
    );
    done();
  });

  test('handleSelectAll is called when select all checkbox is clicked', async done => {
    const handleSelectAll = jest.spyOn(_UsersList.prototype, 'handleSelectAll');
    const wrapper = mountWithContexts(<UsersList />);
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === false
    );
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('selected').length === 2
    );
    done();
  });

  test('delete button is disabled if user does not have delete capabilities on a selected user', async done => {
    const wrapper = mountWithContexts(<UsersList />);
    wrapper.find('UsersList').setState({
      users: mockUsers,
      itemCount: 2,
      isInitialized: true,
      selected: mockUsers.slice(0, 1),
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === false
    );
    wrapper.find('UsersList').setState({
      selected: mockUsers,
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === true
    );
    done();
  });

  test('api is called to delete users for each selected user.', () => {
    UsersAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<UsersList />);
    wrapper.find('UsersList').setState({
      users: mockUsers,
      itemCount: 2,
      isInitialized: true,
      isModalOpen: true,
      selected: mockUsers,
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(UsersAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('error is shown when user not successfully deleted from api', async done => {
    UsersAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/users/1',
          },
          data: 'An error occurred',
        },
      })
    );
    const wrapper = mountWithContexts(<UsersList />);
    wrapper.find('UsersList').setState({
      users: mockUsers,
      itemCount: 1,
      isInitialized: true,
      isModalOpen: true,
      selected: mockUsers.slice(0, 1),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    done();
  });

  test('Add button shown for users without ability to POST', async done => {
    const wrapper = mountWithContexts(<UsersList />);
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    done();
  });

  test('Add button hidden for users without ability to POST', async done => {
    UsersAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    const wrapper = mountWithContexts(<UsersList />);
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'UsersList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    done();
  });
});
