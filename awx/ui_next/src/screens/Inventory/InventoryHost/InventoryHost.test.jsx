import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockHost from '../shared/data.host.json';
import InventoryHost from './InventoryHost';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/inventories/inventory/1/hosts/1',
    params: { id: 1, hostId: 1 },
  }),
}));

InventoriesAPI.readHostDetail.mockResolvedValue({
  data: { ...mockHost },
});

const mockInventory = {
  id: 1,
  name: 'Mock Inventory',
};

describe('<InventoryHost />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHost inventory={mockInventory} setBreadcrumb={() => {}} />
      );
    });
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('should render expected tabs', async () => {
    const expectedTabs = [
      'Back to Hosts',
      'Details',
      'Facts',
      'Groups',
      'Completed Jobs',
    ];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readHostDetail.mockRejectedValueOnce(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHost inventory={mockInventory} setBreadcrumb={() => {}} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHost inventory={mockInventory} setBreadcrumb={() => {}} />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('should show content error when inventory id does not match host inventory', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHost inventory={{ id: 99 }} setBreadcrumb={() => {}} />
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
