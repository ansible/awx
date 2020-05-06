import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Jobs from './Jobs';

describe('<Jobs />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Jobs />);
  });

  test('should display a breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs'],
    });
    const match = { path: '/jobs', url: '/jobs', isExact: true };

    const wrapper = mountWithContexts(<Jobs />, {
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
