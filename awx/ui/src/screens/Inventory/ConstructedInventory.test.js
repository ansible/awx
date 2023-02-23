import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { ConstructedInventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockInventory from './shared/data.inventory.json';
import ConstructedInventory from './ConstructedInventory';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/constructed_inventories/1',
    params: { id: 1 },
  }),
}));

describe('<ConstructedInventory />', () => {
  let wrapper;

  test('should render expected tabs', async () => {
    ConstructedInventoriesAPI.readDetail.mockResolvedValue({
      data: mockInventory,
    });
    const expectedTabs = [
      'Back to Inventories',
      'Details',
      'Access',
      'Hosts',
      'Groups',
      'Jobs',
      'Job Templates',
    ];
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventory setBreadcrumb={() => {}} />
      );
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    ConstructedInventoriesAPI.readDetail.mockResolvedValue({
      data: { ...mockInventory, kind: 'constructed' },
    });
    const history = createMemoryHistory({
      initialEntries: ['/inventories/constructed_inventory/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventory setBreadcrumb={() => {}} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/inventories/constructed_inventory/1/foobar',
                  path: '/inventories/:inventoryType/:id/foobar',
                },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
