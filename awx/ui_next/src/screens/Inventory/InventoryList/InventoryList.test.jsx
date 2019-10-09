import React from 'react';
import { InventoriesAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import InventoriesList, { _InventoriesList } from './InventoryList';

jest.mock('@api');

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

describe('<InventoriesList />', () => {
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
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <InventoriesList
        match={{ path: '/inventories', url: '/inventories' }}
        location={{ search: '', pathname: '/inventories' }}
      />
    );
  });

  test('Inventories are retrieved from the api and the components finishes loading', async done => {
    const loadInventories = jest.spyOn(
      _InventoriesList.prototype,
      'loadInventories'
    );
    const wrapper = mountWithContexts(<InventoriesList />);
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === true
    );
    expect(loadInventories).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('InventoryListItem').length).toBe(3);
    done();
  });

  test('handleSelect is called when a inventory list item is selected', async done => {
    const handleSelect = jest.spyOn(_InventoriesList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<InventoriesList />);
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === false
    );
    await wrapper
      .find('input#select-inventory-1')
      .closest('DataListCheck')
      .props()
      .onChange();
    expect(handleSelect).toBeCalled();
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('selected').length === 1
    );
    done();
  });

  test('handleSelectAll is called when a inventory list item is selected', async done => {
    const handleSelectAll = jest.spyOn(
      _InventoriesList.prototype,
      'handleSelectAll'
    );
    const wrapper = mountWithContexts(<InventoriesList />);
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === false
    );
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('selected').length === 3
    );
    done();
  });

  test('delete button is disabled if user does not have delete capabilities on a selected inventory', async done => {
    const wrapper = mountWithContexts(<InventoriesList />);
    wrapper.find('InventoriesList').setState({
      inventories: mockInventories,
      itemCount: 3,
      isInitialized: true,
      selected: mockInventories.slice(0, 2),
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === false
    );
    wrapper.find('InventoriesList').setState({
      selected: mockInventories,
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === true
    );
    done();
  });

  test('api is called to delete inventories for each selected inventory.', () => {
    InventoriesAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<InventoriesList />);
    wrapper.find('InventoriesList').setState({
      inventories: mockInventories,
      itemCount: 3,
      isInitialized: true,
      isModalOpen: true,
      selected: mockInventories.slice(0, 2),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(InventoriesAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('error is shown when inventory not successfully deleted from api', async done => {
    InventoriesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/inventories/1',
          },
          data: 'An error occurred',
        },
      })
    );
    const wrapper = mountWithContexts(<InventoriesList />);
    wrapper.find('InventoriesList').setState({
      inventories: mockInventories,
      itemCount: 1,
      isInitialized: true,
      isModalOpen: true,
      selected: mockInventories.slice(0, 1),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    done();
  });

  test('Add button shown for users without ability to POST', async done => {
    const wrapper = mountWithContexts(<InventoriesList />);
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    done();
  });

  test('Add button hidden for users without ability to POST', async done => {
    InventoriesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    const wrapper = mountWithContexts(<InventoriesList />);
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'InventoriesList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    done();
  });
});
