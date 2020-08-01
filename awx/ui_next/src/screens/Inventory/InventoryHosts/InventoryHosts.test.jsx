import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryHosts from './InventoryHosts';

describe('<InventoryHosts />', () => {
  test('should render inventory host list', () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts'],
    });

    const match = {
      path: '/inventories/inventory/:id/hosts',
      url: '/inventories/inventory/1/hosts',
      isExact: true,
    };

    const wrapper = mountWithContexts(<InventoryHosts />, {
      context: { router: { history, route: { match } } },
    });

    expect(wrapper.find('InventoryHostList').length).toBe(1);
    wrapper.unmount();
  });
});
