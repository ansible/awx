import React from 'react';
import { GroupsAPI } from '@api';
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
      created_by: { id: 1, name: 'Athena' },
      modified_by: { id: 1, name: 'Apollo' },
    },
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
        <InventoryGroup inventory={inventory} setBreadcrumb={() => {}} />,
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
