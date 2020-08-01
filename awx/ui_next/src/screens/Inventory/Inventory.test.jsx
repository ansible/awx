import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockInventory from './shared/data.inventory.json';
import Inventory from './Inventory';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/inventories/1',
    params: { id: 1 },
  }),
}));

InventoriesAPI.readDetail.mockResolvedValue({
  data: mockInventory,
});

describe('<Inventory />', () => {
  let wrapper;

  test('initially renders succesfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<Inventory setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 7);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Inventory setBreadcrumb={() => {}} />, {
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
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
