import React from 'react';
import { createMemoryHistory } from 'history';
import { UsersAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockDetails from './data.user.json';
import User from './User';

jest.mock('@api');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};

async function getUsers() {
  return {
    count: 1,
    next: null,
    previous: null,
    data: {
      results: [mockDetails],
    },
  };
}

describe('<User />', () => {
  test('initially renders succesfully', () => {
    UsersAPI.readDetail.mockResolvedValue({ data: mockDetails });
    UsersAPI.read.mockImplementation(getUsers);
    mountWithContexts(<User setBreadcrumb={() => {}} me={mockMe} />);
  });

  test('notifications tab shown for admins', async () => {
    UsersAPI.readDetail.mockResolvedValue({ data: mockDetails });
    UsersAPI.read.mockImplementation(getUsers);

    const wrapper = mountWithContexts(
      <User setBreadcrumb={() => {}} me={mockMe} />
    );
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 5);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/users/1/foobar'],
    });
    const wrapper = mountWithContexts(
      <User setBreadcrumb={() => {}} me={mockMe} />,
      {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/users/1/foobar',
                path: '/users/1/foobar',
              },
            },
          },
        },
      }
    );
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
