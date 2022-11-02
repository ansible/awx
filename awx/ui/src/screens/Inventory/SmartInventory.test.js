import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockSmartInventory from './shared/data.smart_inventory.json';
import SmartInventory from './SmartInventory';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/inventories/smart_inventory/1',
    params: { id: 1 },
  }),
}));

describe('<SmartInventory />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    InventoriesAPI.readDetail.mockResolvedValue({
      data: mockSmartInventory,
    });
    await act(async () => {
      wrapper = mountWithContexts(<SmartInventory setBreadcrumb={() => {}} />);
    });
    wrapper.update();
    expect(wrapper.find('SmartInventory').length).toBe(1);
    expect(wrapper.find('RoutedTabs li').length).toBe(6);
  });

  test('should render expected tabs', async () => {
    const expectedTabs = [
      'Back to Inventories',
      'Details',
      'Access',
      'Hosts',
      'Jobs',
      'Job Templates',
    ];
    await act(async () => {
      wrapper = mountWithContexts(<SmartInventory setBreadcrumb={() => {}} />);
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when api throws an error', async () => {
    const error = new Error();
    error.response = { status: 404 };
    InventoriesAPI.readDetail.mockRejectedValueOnce(error);
    await act(async () => {
      wrapper = mountWithContexts(<SmartInventory setBreadcrumb={() => {}} />);
    });
    expect(InventoriesAPI.readDetail).toHaveBeenCalledTimes(1);
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual('Not Found');
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<SmartInventory setBreadcrumb={() => {}} />, {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/inventories/smart_inventory/1/foobar',
                path: '/inventories/smart_inventory/1/foobar',
              },
            },
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
