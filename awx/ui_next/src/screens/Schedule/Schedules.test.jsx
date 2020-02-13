import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { createMemoryHistory } from 'history';
import Schedules from './Schedules';

describe('<Schedules />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders succesfully', () => {
    wrapper = mountWithContexts(<Schedules />);
  });

  test('should display schedule list breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/schedules'],
    });

    wrapper = mountWithContexts(<Schedules />, {
      context: {
        router: {
          history,
          route: {
            location: history.location,
          },
        },
      },
    });

    expect(wrapper.find('Crumb').length).toBe(1);
    expect(wrapper.find('BreadcrumbHeading').text()).toBe('Schedules');
  });
});
