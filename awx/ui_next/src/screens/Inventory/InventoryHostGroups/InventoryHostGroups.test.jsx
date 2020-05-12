import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { HostsAPI } from '../../../api';
import InventoryHostGroups from './InventoryHostGroups';

jest.mock('../../../api');
HostsAPI.readAllGroups.mockResolvedValue({
  data: {
    count: 1,
    results: [
      {
        id: 1,
        url: 'www.google.com',
        summary_fields: {
          inventory: { id: 1, name: 'foo' },
          user_capabilities: { edit: true },
        },
        name: 'Bar',
      },
    ],
  },
});
HostsAPI.readGroupsOptions.mockResolvedValue({ data: { actions: {} } });

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
