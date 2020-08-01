import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI, OrganizationsAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockInventorySource from '../shared/data.inventory_source.json';
import InventorySource from './InventorySource';

jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/InventorySources');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/inventories/inventory/2/sources/123',
    params: { id: 2, sourceId: 123 },
  }),
}));

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
        <InventorySource
          inventory={mockInventory}
          me={{ is_system_auditor: false }}
          setBreadcrumb={() => {}}
        />
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render expected tabs', () => {
    InventoriesAPI.readSourceDetail.mockResolvedValue({
      data: { ...mockInventorySource },
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1, name: 'isNotifAdmin' }] },
    });
    const expectedTabs = [
      'Back to Sources',
      'Details',
      'Schedules',
      'Notifications',
    ];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readSourceDetail.mockResolvedValue({
      data: { ...mockInventorySource },
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1, name: 'isNotifAdmin' }] },
    });
    InventoriesAPI.readSourceDetail.mockRejectedValueOnce(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySource
          inventory={mockInventory}
          me={{ is_system_auditor: false }}
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
    InventoriesAPI.readSourceDetail.mockResolvedValue({
      data: { ...mockInventorySource },
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1, name: 'isNotifAdmin' }] },
    });
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/2/sources/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySource
          inventory={mockInventory}
          setBreadcrumb={() => {}}
          me={{ is_system_auditor: false }}
        />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual('Not Found');
  });

  test('should call api', () => {
    InventoriesAPI.readSourceDetail.mockResolvedValue({
      data: { ...mockInventorySource },
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1, name: 'isNotifAdmin' }] },
    });
    expect(InventoriesAPI.readSourceDetail).toBeCalledWith(2, 123);
    expect(OrganizationsAPI.read).toBeCalled();
  });

  test('should not render notifications tab', () => {
    InventoriesAPI.readSourceDetail.mockResolvedValue({
      data: { ...mockInventorySource },
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [] },
    });
    expect(wrapper.find('button[aria-label="Notifications"]').length).toBe(0);
  });
});
