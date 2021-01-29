import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import AllSchedules from './AllSchedules';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<AllSchedules />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders succesfully', () => {
    wrapper = mountWithContexts(<AllSchedules />);
  });

  test('should display schedule list breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/schedules'],
    });

    wrapper = mountWithContexts(<AllSchedules />, {
      context: {
        router: {
          history,
          route: {
            location: history.location,
          },
        },
      },
    });

    expect(wrapper.find('Title').text()).toBe('Schedules');
  });
});
