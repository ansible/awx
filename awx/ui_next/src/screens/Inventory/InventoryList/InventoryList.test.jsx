import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import InventoryList from './InventoryList';

jest.mock('../../../api');

const mockInventories = [
  {
    id: 1,
    type: 'inventory',
    url: '/api/v2/inventories/1/',
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
        description: '',
      },
      user_capabilities: {
        edit: true,
        delete: true,
        copy: true,
        adhoc: true,
      },
    },
    created: '2019-10-04T16:56:48.025455Z',
    modified: '2019-10-04T16:56:48.025468Z',
    name: 'Inv no hosts',
    description: '',
    organization: 1,
    kind: '',
    host_filter: null,
    variables: '---',
    has_active_failures: false,
    total_hosts: 0,
    hosts_with_active_failures: 0,
    total_groups: 0,
    groups_with_active_failures: 0,
    has_inventory_sources: false,
    total_inventory_sources: 0,
    inventory_sources_with_failures: 0,
    insights_credential: null,
    pending_deletion: false,
  },
  {
    id: 2,
    type: 'inventory',
    url: '/api/v2/inventories/2/',
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
        description: '',
      },
      user_capabilities: {
        edit: true,
        delete: true,
        copy: true,
        adhoc: true,
      },
    },
    created: '2019-10-04T14:28:04.765571Z',
    modified: '2019-10-04T14:28:04.765594Z',
    name: "Mike's Inventory",
    description: '',
    organization: 1,
    kind: '',
    host_filter: null,
    variables: '---',
    has_active_failures: false,
    total_hosts: 1,
    hosts_with_active_failures: 0,
    total_groups: 0,
    groups_with_active_failures: 0,
    has_inventory_sources: false,
    total_inventory_sources: 0,
    inventory_sources_with_failures: 0,
    insights_credential: null,
    pending_deletion: false,
  },
  {
    id: 3,
    type: 'inventory',
    url: '/api/v2/inventories/3/',
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
        description: '',
      },
      user_capabilities: {
        edit: true,
        delete: false,
        copy: true,
        adhoc: true,
      },
    },
    created: '2019-10-04T15:29:11.542911Z',
    modified: '2019-10-04T15:29:11.542924Z',
    name: 'Smart Inv',
    description: '',
    organization: 1,
    kind: 'smart',
    host_filter: 'search=local',
    variables: '',
    has_active_failures: false,
    total_hosts: 1,
    hosts_with_active_failures: 0,
    total_groups: 0,
    groups_with_active_failures: 0,
    has_inventory_sources: false,
    total_inventory_sources: 0,
    inventory_sources_with_failures: 0,
    insights_credential: null,
    pending_deletion: false,
  },
];

describe('<InventoryList />', () => {
  let debug;
  beforeEach(() => {
    InventoriesAPI.read.mockResolvedValue({
      data: {
        count: mockInventories.length,
        results: mockInventories,
      },
    });

    InventoriesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    jest.clearAllMocks();
    global.console.debug = debug;
  });

  test('should load and render inventories', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    expect(wrapper.find('InventoryListItem')).toHaveLength(3);
  });

  test('should select inventory when checked', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('InventoryListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(
      wrapper
        .find('InventoryListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should select all', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();

    const items = wrapper.find('InventoryListItem');
    expect(items).toHaveLength(3);
    items.forEach(item => {
      expect(item.prop('isSelected')).toEqual(true);
    });

    expect(
      wrapper
        .find('InventoryListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should disable delete button', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('InventoryListItem')
        .at(2)
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(wrapper.find('ToolbarDeleteButton button').prop('disabled')).toEqual(
      true
    );
  });

  test('should call delete api', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('InventoryListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('InventoryListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(InventoriesAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('should show deletion error', async () => {
    InventoriesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/inventory/1',
          },
          data: 'An error occurred',
        },
      })
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('InventoryListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();

    const modal = wrapper.find('Modal[aria-label="Deletion Error"]');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });

  test('Add button shown for users without ability to POST', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('Add button hidden for users without ability to POST', async () => {
    InventoriesAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
          },
        },
      });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<InventoryList />);
    });
    wrapper.update();

    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
