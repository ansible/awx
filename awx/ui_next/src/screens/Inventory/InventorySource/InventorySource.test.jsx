import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockInventorySource from '../shared/data.inventory_source.json';
import InventorySource from './InventorySource';

jest.mock('@api/models/Inventories');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/inventories/inventory/2/sources/123',
    params: { id: 2, sourceId: 123 },
  }),
}));

InventoriesAPI.readSourceDetail.mockResolvedValue({
  data: { ...mockInventorySource },
});

const mockInventory = {
  id: 2,
  name: 'Mock Inventory',
};

describe('<InventorySource />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySource inventory={mockInventory} setBreadcrumb={() => {}} />
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should render expected tabs', () => {
    const expectedTabs = [
      'Back to Sources',
      'Details',
      'Notifications',
      'Schedules',
    ];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readSourceDetail.mockRejectedValueOnce(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySource inventory={mockInventory} setBreadcrumb={() => {}} />
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
      initialEntries: ['/inventories/inventory/2/sources/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySource inventory={mockInventory} setBreadcrumb={() => {}} />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual('Not Found');
  });
});
