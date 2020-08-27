import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserAdd from './UserAdd';
import { OrganizationsAPI } from '../../../api';

jest.mock('../../../api');
let wrapper;

describe('<UserAdd />', () => {
  test('handleSubmit should post to api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<UserAdd />);
    });
    OrganizationsAPI.createUser.mockResolvedValueOnce({ data: {} });
    const updatedUserData = {
      username: 'sysadmin',
      email: 'sysadmin@ansible.com',
      first_name: 'System',
      last_name: 'Administrator',
      password: 'password',
      organization: 1,
      is_superuser: true,
      is_system_auditor: false,
    };
    await act(async () => {
      wrapper.find('UserForm').prop('handleSubmit')(updatedUserData);
    });

    const { organization, ...userData } = updatedUserData;
    expect(OrganizationsAPI.createUser.mock.calls).toEqual([
      [organization, userData],
    ]);
  });

  test('should navigate to users list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    await act(async () => {
      wrapper = mountWithContexts(<UserAdd />, {
        context: { router: { history } },
      });
    });
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual('/users');
  });

  test('successful form submission should trigger redirect', async () => {
    const history = createMemoryHistory({});
    const userData = {
      username: 'sysadmin',
      email: 'sysadmin@ansible.com',
      first_name: 'System',
      last_name: 'Administrator',
      password: 'password',
      organization: 1,
      is_superuser: true,
      is_system_auditor: false,
    };
    OrganizationsAPI.createUser.mockResolvedValueOnce({
      data: {
        id: 5,
        ...userData,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<UserAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      wrapper.find('UserForm').prop('handleSubmit')(userData);
    });
    expect(history.location.pathname).toEqual('/users/5/details');
  });
});
