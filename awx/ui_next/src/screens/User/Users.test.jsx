import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Users from './Users';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Users />', () => {
  test('initially renders successfully', () => {
    const wrapper = mountWithContexts(<Users />);
    wrapper.unmount();
  });

  test('should display a breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/users'],
    });
    const match = { path: '/users', url: '/users', isExact: true };

    const wrapper = mountWithContexts(<Users />, {
      context: {
        router: {
          history,
          route: {
            location: history.location,
            match,
          },
        },
      },
    });
    expect(wrapper.find('Title').length).toBe(1);
    wrapper.unmount();
  });
});
