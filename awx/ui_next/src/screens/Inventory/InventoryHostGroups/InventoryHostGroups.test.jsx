import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import InventoryHostGroups from './InventoryHostGroups';

jest.mock('@api');

describe('<InventoryHostGroups />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts/1/groups'],
    });

    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostGroups />, {
        context: {
          router: { history, route: { location: history.location } },
        },
      });
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('InventoryHostGroupsList').length).toBe(1);
  });
});
