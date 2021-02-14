import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Projects from './Projects';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Projects />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Projects />);
  });

  test('should display a breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/projects'],
    });
    const match = { path: '/projects', url: '/projects', isExact: true };

    const wrapper = mountWithContexts(<Projects />, {
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
