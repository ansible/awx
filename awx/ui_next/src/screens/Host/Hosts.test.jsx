import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

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

  test('should render Host component', () => {
    const history = createMemoryHistory({
      initialEntries: ['/hosts/1'],
    });

    const match = {
      path: '/hosts/:id',
      url: '/hosts/1',
      isExact: true,
    };

    const wrapper = mountWithContexts(<Hosts />, {
      context: { router: { history, route: { match } } },
    });

    expect(wrapper.find('Host').length).toBe(1);
    wrapper.unmount();
  });
});
