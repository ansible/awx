import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Users from './Users';

describe('<Users />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(<Users />);
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
    expect(wrapper.find('BreadcrumbHeading').length).toBe(1);
    wrapper.unmount();
  });
});
