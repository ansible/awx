import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Jobs from './Jobs';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

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
    expect(wrapper.find('Title').length).toBe(1);
    wrapper.unmount();
  });
});
