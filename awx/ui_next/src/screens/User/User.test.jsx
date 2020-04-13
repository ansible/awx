import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { UsersAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockDetails from './data.user.json';
import User from './User';

jest.mock('@api');

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
  test('initially renders successfully', async () => {
    UsersAPI.readDetail.mockResolvedValue({ data: mockDetails });
    UsersAPI.read.mockImplementation(getUsers);
    const history = createMemoryHistory({
      initialEntries: ['/users/1'],
    });
    await act(async () => {
      mountWithContexts(<User setBreadcrumb={() => {}} />, {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/users/1',
                path: '/users/1',
              },
            },
          },
        },
      });
    });
  });

  test('tabs shown for users', async () => {
    UsersAPI.readDetail.mockResolvedValue({ data: mockDetails });
    UsersAPI.read.mockImplementation(getUsers);
    const history = createMemoryHistory({
      initialEntries: ['/users/1'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<User setBreadcrumb={() => {}} />, {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/users/1',
                path: '/users/1',
              },
            },
          },
        },
      });
    });
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 5);

    /* eslint-disable react/button-has-type */
    expect(
      wrapper
        .find('Tabs')
        .containsAllMatchingElements([
          <button aria-label="Details">Details</button>,
          <button aria-label="Organizations">Organizations</button>,
          <button aria-label="Teams">Teams</button>,
          <button aria-label="Access">Access</button>,
          <button aria-label="Tokens">Tokens</button>,
        ])
    ).toEqual(true);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/users/1/foobar'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<User setBreadcrumb={() => {}} />, {
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
      });
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
