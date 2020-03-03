import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { GroupsAPI, InventoriesAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import InventoryGroupHostList from './InventoryGroupHostList';
import mockHosts from '../shared/data.hosts.json';

jest.mock('@api/models/Groups');
jest.mock('@api/models/Inventories');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    groupId: 2,
  }),
}));

describe('<InventoryGroupHostList />', () => {
  let wrapper;

  beforeEach(async () => {
    GroupsAPI.readAllHosts.mockResolvedValue({
      data: { ...mockHosts },
    });
    InventoriesAPI.readHostsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupHostList />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders successfully ', () => {
    expect(wrapper.find('InventoryGroupHostList').length).toBe(1);
  });

  test('should fetch inventory group hosts from api and render them in the list', () => {
    expect(GroupsAPI.readAllHosts).toHaveBeenCalled();
    expect(InventoriesAPI.readHostsOptions).toHaveBeenCalled();
    expect(wrapper.find('InventoryGroupHostListItem').length).toBe(3);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('DataListCheck[id="select-host-2"]').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-host-2"]').invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-host-2"]').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-host-2"]').invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-host-2"]').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
  });

  test('should show add dropdown button according to permissions', async () => {
    expect(wrapper.find('AddHostDropdown').length).toBe(1);
    InventoriesAPI.readHostsOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupHostList />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('AddHostDropdown').length).toBe(0);
  });

  test('should show associate host modal when adding an existing host', () => {
    const dropdownToggle = wrapper.find(
      'DropdownToggle button[aria-label="add host"]'
    );
    dropdownToggle.simulate('click');
    wrapper
      .find('DropdownItem[aria-label="add existing host"]')
      .simulate('click');
    expect(wrapper.find('AlertModal').length).toBe(1);
    wrapper.find('ModalBoxCloseButton').simulate('click');
    expect(wrapper.find('AlertModal').length).toBe(0);
  });

  test('should navigate to host add form when adding a new host', async () => {
    GroupsAPI.readAllHosts.mockResolvedValue({
      data: { ...mockHosts },
    });
    InventoriesAPI.readHostsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    const history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupHostList />, {
        context: {
          router: { history },
        },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const dropdownToggle = wrapper.find(
      'DropdownToggle button[aria-label="add host"]'
    );
    dropdownToggle.simulate('click');
    wrapper.find('DropdownItem[aria-label="add new host"]').simulate('click');
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/groups/2/nested_hosts/add'
    );
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readHostsOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupHostList />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
