import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from 'api';
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

describe('<Inventory />', () => {
  let wrapper;

  beforeEach(async () => {
    InventoriesAPI.readDetail.mockResolvedValue({
      data: mockInventory,
    });
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<Inventory setBreadcrumb={() => {}} />);
    });
    wrapper.update();
    expect(wrapper.find('Inventory').length).toBe(1);
    expect(wrapper.find('RoutedTabs li').length).toBe(8);
  });

  test('should render expected tabs', async () => {
    const expectedTabs = [
      'Back to Inventories',
      'Details',
      'Access',
      'Groups',
      'Hosts',
      'Jobs',
      'Job Templates',
    ];
    await act(async () => {
      wrapper = mountWithContexts(<Inventory setBreadcrumb={() => {}} />);
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
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
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
