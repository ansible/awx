import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import UserOrganizations from './UserOrganizations';

describe('<UserOrganizations />', () => {
  test('userOrganizations mounts successfully', () => {
    const history = createMemoryHistory({
      initialEntries: ['/users/1/organizations'],
    });
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <Route
          path="/users/:id/organizations"
          component={() => <UserOrganizations />}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
    waitForElement(wrapper, 'UserOrganizationList');
  });
});
