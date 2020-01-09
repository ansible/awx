import React from 'react';
import { GroupsAPI } from '@api';
import { Route } from 'react-router-dom';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import InventoryGroup from './InventoryGroup';

jest.mock('@api');
GroupsAPI.readDetail.mockResolvedValue({
  data: {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    variables: 'bizz: buzz',
    summary_fields: {
      inventory: { id: 1 },
      created_by: { id: 1, username: 'Athena' },
      modified_by: { id: 1, username: 'Apollo' },
    },
    created: '2020-04-25T01:23:45.678901Z',
    modified: '2020-04-25T01:23:45.678901Z',
  },
});
describe('<InventoryGroup />', () => {
  let wrapper;
  let history;
  const inventory = { id: 1, name: 'Foo' };
  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/1/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/inventories/inventory/:id/groups"
          component={() => (
            <InventoryGroup setBreadcrumb={() => {}} inventory={inventory} />
          )}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('renders successfully', async () => {
    expect(wrapper.length).toBe(1);
  });
  test('expect all tabs to exist, including Return to Groups', async () => {
    expect(wrapper.find('button[aria-label="Return to Groups"]').length).toBe(
      1
    );
    expect(wrapper.find('button[aria-label="Details"]').length).toBe(1);
    expect(wrapper.find('button[aria-label="Related Groups"]').length).toBe(1);
    expect(wrapper.find('button[aria-label="Hosts"]').length).toBe(1);
  });
});
