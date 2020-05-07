import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { UsersAPI } from '@api';
import { Route } from 'react-router-dom';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import UserAccessList from './UserAccessList';

jest.mock('@api/models/Users');
describe('<UserAccessList />', () => {
  test('should render properly', async () => {
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
            },
          },
          {
            id: 3,
            name: 'Update',
            type: 'role',
            url: '/api/v2/roles/258/',
            summary_fields: {
              resource_name: 'Foo Bar',
              resource_id: 75,
              resource_type: 'credential',
              resource_type_display_name: 'Credential',
              user_capabilities: { unattach: true },
            },
          },
        ],
        count: 2,
      },
    });

    UsersAPI.roleOptions.mockResolvedValue({
      data: { actions: { POST: { id: 1, disassociate: true } } },
    });

    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/users/18/access'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/users/:id/access">
          <UserAccessList />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 18 } },
              },
            },
          },
        }
      );
    });

    expect(wrapper.find('UserAccessList').length).toBe(1);
  });
});
