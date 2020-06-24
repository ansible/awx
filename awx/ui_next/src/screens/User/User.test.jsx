import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { UsersAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockDetails from './data.user.json';
import User from './User';

jest.mock('../../api');

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
      wrapper = mountWithContexts(
        <User me={{ id: 1 }} setBreadcrumb={() => {}} />,
        {
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
        }
      );
    });
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 6);

    /* eslint-disable react/button-has-type */
    expect(wrapper.find('Tabs TabButton').length).toEqual(6);
  });

  test('should not now Tokens tab', async () => {
    UsersAPI.readDetail.mockResolvedValue({ data: mockDetails });
    UsersAPI.read.mockImplementation(getUsers);
    const history = createMemoryHistory({
      initialEntries: ['/users/1'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <User me={{ id: 2 }} setBreadcrumb={() => {}} />,
        {
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
        }
      );
    });
    expect(wrapper.find('button[aria-label="Tokens"]').length).toBe(0);
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
