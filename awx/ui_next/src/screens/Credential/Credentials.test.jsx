import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Credentials from './Credentials';

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

    expect(wrapper.find('Crumb').length).toBe(1);
    expect(wrapper.find('BreadcrumbHeading').text()).toBe('Credentials');
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
    expect(wrapper.find('BreadcrumbHeading').text()).toBe(
      'Create New Credential'
    );
  });
});
