import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { UsersAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import UserEdit from './UserEdit';

jest.mock('../../../api');
let wrapper;

describe('<UserEdit />', () => {
  const mockData = {
    id: 1,
    username: 'sysadmin',
    email: 'sysadmin@ansible.com',
    first_name: 'System',
    last_name: 'Administrator',
    password: 'password',
    organization: 1,
    is_superuser: true,
    is_system_auditor: false,
  };

  test('handleSubmit should call api update', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UserEdit user={mockData} />);
    });

    const updatedUserData = {
      ...mockData,
      username: 'Foo',
    };
    await act(async () => {
      wrapper.find('UserForm').prop('handleSubmit')(updatedUserData);
    });

    expect(UsersAPI.update).toHaveBeenCalledWith(1, updatedUserData);
  });

  test('should navigate to user detail when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    await act(async () => {
      wrapper = mountWithContexts(<UserEdit user={mockData} />, {
        context: { router: { history } },
      });
    });

    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });

    expect(history.location.pathname).toEqual('/users/1/details');
  });
});
