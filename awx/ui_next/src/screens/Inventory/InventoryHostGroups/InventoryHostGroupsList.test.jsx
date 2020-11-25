import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { HostsAPI, InventoriesAPI } from '../../../api';
import InventoryHostGroupsList from './InventoryHostGroupsList';

jest.mock('../../../api');

const mockGroups = [
  {
    id: 1,
    type: 'group',
    name: 'foo',
    inventory: 1,
    url: '/api/v2/groups/1',
    summary_fields: {
      inventory: {
        id: 1,
      },
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 2,
    type: 'group',
    name: 'bar',
    inventory: 1,
    url: '/api/v2/groups/2',
    summary_fields: {
      inventory: {
        id: 1,
      },
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 3,
    type: 'group',
    name: 'baz',
    inventory: 1,
    url: '/api/v2/groups/3',
    summary_fields: {
      inventory: {
        id: 1,
      },
      user_capabilities: {
        delete: true,
        edit: false,
      },
    },
  },
];

describe('<InventoryHostGroupsList />', () => {
  let wrapper;

  beforeEach(async () => {
    HostsAPI.readAllGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    HostsAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts/3/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/inventory/:id/hosts/:hostId/groups">
          <InventoryHostGroupsList />
        </Route>,
        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('InventoryHostGroupsList').length).toBe(1);
  });

  test('should fetch groups from api and render them in the list', async () => {
    expect(HostsAPI.readAllGroups).toHaveBeenCalled();
    expect(wrapper.find('InventoryHostGroupItem').length).toBe(3);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(false);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')(
        true
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(true);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')(
        false
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
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

  test('should show content error when api throws error on initial render', async () => {
    HostsAPI.readAllGroups.mockImplementation(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostGroupsList />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('should show add button according to permissions', async () => {
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    HostsAPI.readGroupsOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostGroupsList />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });

  test('should show associate group modal when adding an existing group', () => {
    wrapper.find('ToolbarAddButton').simulate('click');
    expect(wrapper.find('AssociateModal').length).toBe(1);
    wrapper.find('ModalBoxCloseButton').simulate('click');
    expect(wrapper.find('AssociateModal').length).toBe(0);
  });

  test('should make expected api request when associating groups', async () => {
    HostsAPI.associateGroup.mockResolvedValue();
    InventoriesAPI.readGroups.mockResolvedValue({
      data: {
        count: 1,
        results: [{ id: 123, name: 'foo', url: '/api/v2/groups/123/' }],
      },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper.find('ToolbarAddButton').simulate('click');
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    wrapper.update();
    await act(async () => {
      wrapper
        .find('CheckboxListItem')
        .first()
        .invoke('onSelect')();
    });
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    await waitForElement(wrapper, 'AssociateModal', el => el.length === 0);
    expect(InventoriesAPI.readGroups).toHaveBeenCalledTimes(1);
    expect(HostsAPI.associateGroup).toHaveBeenCalledTimes(1);
  });

  test('expected api calls are made for multi-disassociation', async () => {
    expect(HostsAPI.disassociateGroup).toHaveBeenCalledTimes(0);
    expect(HostsAPI.readAllGroups).toHaveBeenCalledTimes(1);
    expect(wrapper.find('DataListCheck').length).toBe(3);
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
    wrapper.find('button[aria-label="Disassociate"]').simulate('click');
    expect(wrapper.find('AlertModal Title').text()).toEqual(
      'Disassociate group from host?'
    );
    await act(async () => {
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .simulate('click');
    });
    expect(HostsAPI.disassociateGroup).toHaveBeenCalledTimes(3);
    expect(HostsAPI.readAllGroups).toHaveBeenCalledTimes(2);
  });

  test('should show error modal for failed disassociation', async () => {
    HostsAPI.disassociateGroup.mockRejectedValue(new Error());
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('button[aria-label="Disassociate"]').simulate('click');
    expect(wrapper.find('AlertModal Title').text()).toEqual(
      'Disassociate group from host?'
    );
    await act(async () => {
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('AlertModal ErrorDetail').length).toBe(1);
  });
});
