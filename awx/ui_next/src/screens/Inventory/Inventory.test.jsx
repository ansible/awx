import React from 'react';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockInventory from './shared/data.inventory.json';
import Inventory from './Inventory';

jest.mock('@api');

InventoriesAPI.readDetail.mockResolvedValue({
  data: mockInventory,
});

describe.only('<Inventory />', () => {
  test('initially renders succesfully', async done => {
    const wrapper = mountWithContexts(
      <Inventory setBreadcrumb={() => {}} match={{ params: { id: 1 } }} />
    );
    await waitForElement(
      wrapper,
      'Inventory',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'Inventory',
      el => el.state('hasContentLoading') === false
    );
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 6);
    done();
  });
  test('should show content error when user attempts to navigate to erroneous route', async done => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/foobar'],
    });
    const wrapper = mountWithContexts(<Inventory setBreadcrumb={() => {}} />, {
      context: {
        router: {
          history,
          route: {
            location: history.location,
            match: {
              params: { id: 1 },
              url: '/inventories/inventory/1/foobar',
              path: '/inventories/inventory/1/foobar',
            },
          },
        },
      },
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    done();
  });
});
