import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { GroupsAPI, InventoriesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryGroupHostList from './InventoryGroupHostList';
import mockHosts from '../shared/data.hosts.json';

jest.mock('../../../api/models/Groups');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/CredentialTypes');
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
    expect(wrapper.find('AddDropDownButton').length).toBe(1);
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
    expect(wrapper.find('AddDropDownButton').length).toBe(0);
  });

  test('expected api calls are made for multi-delete', async () => {
    expect(GroupsAPI.disassociateHost).toHaveBeenCalledTimes(0);
    expect(GroupsAPI.readAllHosts).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('button[aria-label="Disassociate"]').simulate('click');
    expect(wrapper.find('AlertModal Title').text()).toEqual(
      'Disassociate host from group?'
    );
    await act(async () => {
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .simulate('click');
    });
    expect(GroupsAPI.disassociateHost).toHaveBeenCalledTimes(3);
    expect(GroupsAPI.readAllHosts).toHaveBeenCalledTimes(2);
  });

  test('should show error modal for failed disassociation', async () => {
    GroupsAPI.disassociateHost.mockRejectedValue(new Error());
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('button[aria-label="Disassociate"]').simulate('click');
    expect(wrapper.find('AlertModal Title').text()).toEqual(
      'Disassociate host from group?'
    );
    await act(async () => {
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('AlertModal ErrorDetail').length).toBe(1);
    expect(wrapper.find('AlertModal ModalBoxBody').text()).toEqual(
      expect.stringContaining('Failed to disassociate one or more hosts.')
    );
  });

  test('should show associate host modal when adding an existing host', () => {
    const dropdownToggle = wrapper.find(
      'ToolbarAddButton button[aria-label="Add"]'
    );
    dropdownToggle.simulate('click');

    wrapper
      .find('DropdownItem[aria-label="Add existing host"]')
      .simulate('click');
    expect(wrapper.find('AssociateModal').length).toBe(1);
    wrapper.find('ModalBoxCloseButton').simulate('click');
    expect(wrapper.find('AssociateModal').length).toBe(0);
  });

  test('should make expected api request when associating hosts', async () => {
    GroupsAPI.associateHost.mockResolvedValue();
    InventoriesAPI.readHosts.mockResolvedValue({
      data: {
        count: 1,
        results: [{ id: 123, name: 'foo', url: '/api/v2/hosts/123/' }],
      },
    });
    wrapper.find('ToolbarAddButton button[aria-label="Add"]').simulate('click');
    await act(async () => {
      wrapper
        .find('DropdownItem[aria-label="Add existing host"]')
        .simulate('click');
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper
        .find('CheckboxListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    await waitForElement(wrapper, 'AssociateModal', el => el.length === 0);
    expect(InventoriesAPI.readHosts).toHaveBeenCalledTimes(1);
    expect(GroupsAPI.associateHost).toHaveBeenCalledTimes(1);
  });

  test('should show error modal for failed host association', async () => {
    GroupsAPI.associateHost.mockRejectedValue(new Error());
    InventoriesAPI.readHosts.mockResolvedValue({
      data: {
        count: 1,
        results: [{ id: 123, name: 'foo', url: '/api/v2/hosts/123/' }],
      },
    });
    wrapper.find('ToolbarAddButton[aria-label="Add"]').simulate('click');
    await act(async () => {
      wrapper
        .find('DropdownItem[aria-label="Add existing host"]')
        .simulate('click');
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await act(async () => {
      wrapper
        .find('CheckboxListItem')
        .first()
        .invoke('onSelect')();
    });
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('AlertModal ErrorDetail').length).toBe(1);
    expect(wrapper.find('AlertModal ModalBoxBody').text()).toEqual(
      expect.stringContaining('Failed to associate.')
    );
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
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/2/nested_hosts/add'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupHostList />, {
        context: {
          router: { history },
        },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const dropdownToggle = wrapper.find(
      'ToolbarAddButton button[aria-label="Add"]'
    );
    dropdownToggle.simulate('click');
    wrapper.find('DropdownItem[aria-label="Add new host"]').simulate('click');
    wrapper.update();
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
