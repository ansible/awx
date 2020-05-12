import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryGroupHosts from './InventoryGroupHosts';

jest.mock('../../../api');

describe('<InventoryGroupHosts />', () => {
  let wrapper;

  test('initially renders successfully', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/1/nested_hosts'],
    });

    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupHosts />, {
        context: {
          router: { history, route: { location: history.location } },
        },
      });
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('InventoryGroupHostList').length).toBe(1);
  });
});
