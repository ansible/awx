import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockHost from '../shared/data.host.json';
import SmartInventoryHost from './SmartInventoryHost';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    params: { id: 1234, hostId: 2 },
    path: '/inventories/smart_inventory/:id/hosts/:hostId',
    url: '/inventories/smart_inventory/1234/hosts/2',
  }),
}));

const mockSmartInventory = {
  id: 1234,
  name: 'Mock Smart Inventory',
};

describe('<SmartInventoryHost />', () => {
  let wrapper;
  let history;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render expected tabs', async () => {
    InventoriesAPI.readHostDetail.mockResolvedValue({
      data: { ...mockHost },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryHost
          inventory={mockSmartInventory}
          setBreadcrumb={() => {}}
        />
      );
    });

    const expectedTabs = ['Back to Hosts', 'Details'];

    expect(wrapper.find('RoutedTabs li').length).toBe(2);
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readHostDetail.mockRejectedValueOnce(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryHost
          inventory={mockSmartInventory}
          setBreadcrumb={() => {}}
        />
      );
    });

    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual(
      'Something went wrong...'
    );
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/smart_inventory/1/hosts/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryHost
          inventory={mockSmartInventory}
          setBreadcrumb={() => {}}
        />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual('Not Found');
  });
});
