import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import Hosts from './Hosts';

describe('<Hosts />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Hosts />);
  });

  test('should display a breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/hosts'],
    });
    const match = { path: '/hosts', url: '/hosts', isExact: true };

    const wrapper = mountWithContexts(<Hosts />, {
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
