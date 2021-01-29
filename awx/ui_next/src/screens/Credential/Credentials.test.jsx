import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Credentials from './Credentials';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Credentials />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders succesfully', () => {
    wrapper = mountWithContexts(<Credentials />);
  });

  test('should display credential list breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/credentials'],
    });

    wrapper = mountWithContexts(<Credentials />, {
      context: {
        router: {
          history,
          route: {
            location: history.location,
          },
        },
      },
    });

    expect(wrapper.find('Crumb').length).toBe(0);
    expect(wrapper.find('Title').text()).toBe('Credentials');
  });

  test('should display create new credential breadcrumb heading', () => {
    const history = createMemoryHistory({
      initialEntries: ['/credentials/add'],
    });

    wrapper = mountWithContexts(<Credentials />, {
      context: {
        router: {
          history,
          route: {
            location: history.location,
          },
        },
      },
    });

    expect(wrapper.find('Crumb').length).toBe(2);
    expect(wrapper.find('Title').text()).toBe('Create New Credential');
  });
});
