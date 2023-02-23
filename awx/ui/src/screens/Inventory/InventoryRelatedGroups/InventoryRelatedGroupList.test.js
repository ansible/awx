import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { Route } from 'react-router-dom';
import { GroupsAPI, InventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryRelatedGroupList from './InventoryRelatedGroupList';
import mockRelatedGroups from '../shared/data.relatedGroups.json';

jest.mock('../../../api/models/Groups');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/CredentialTypes');

const mockGroups = [
  {
    id: 1,
    type: 'group',
    name: 'foo',
    inventory: 1,
    url: '/api/v2/groups/1',
    summary_fields: {
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
      user_capabilities: {
        delete: false,
        edit: false,
      },
    },
  },
];

describe('<InventoryRelatedGroupList />', () => {
  let wrapper;
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 2,
      groupId: 2,
      inventoryType: 'inventory',
    }),
  }));

  beforeEach(async () => {
    GroupsAPI.readChildren.mockResolvedValue({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [
          'parents__search',
          'inventory__search',
          'inventory_sources__search',
          'created_by__search',
          'children__search',
          'modified_by__search',
          'hosts__search',
        ],
      },
    });
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            module_name: {
              choices: [
                ['command', 'command'],
                ['shell', 'shell'],
              ],
            },
          },
          POST: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully ', () => {
    expect(wrapper.find('InventoryRelatedGroupList').length).toBe(1);
  });

  test('should fetch inventory group hosts from api and render them in the list', () => {
    expect(GroupsAPI.readChildren).toHaveBeenCalled();
    expect(InventoriesAPI.readGroupsOptions).toHaveBeenCalled();
    expect(wrapper.find('InventoryRelatedGroupListItem').length).toBe(3);
  });

  test('should render Run Commands Button', async () => {
    expect(wrapper.find('AdHocCommands')).toHaveLength(1);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('input[aria-label="Select row 0"]').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('input[aria-label="Select row 0"]').invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper.find('input[aria-label="Select row 0"]').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('input[aria-label="Select row 0"]').invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper.find('input[aria-label="Select row 0"]').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    wrapper.find('DataListCheck').forEach((el) => {
      expect(el.props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach((el) => {
      expect(el.props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach((el) => {
      expect(el.props().checked).toBe(false);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    GroupsAPI.readChildren.mockResolvedValueOnce({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });

  test('should show add dropdown button according to permissions', async () => {
    GroupsAPI.readChildren.mockResolvedValueOnce({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [
          'parents__search',
          'inventory__search',
          'inventory_sources__search',
          'created_by__search',
          'children__search',
          'modified_by__search',
          'hosts__search',
        ],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('AddDropdown').length).toBe(0);
  });

  test('should associate existing group', async () => {
    GroupsAPI.readPotentialGroups.mockResolvedValue({
      data: { count: mockGroups.length, results: mockGroups },
    });
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/2/groups/2/nested_groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/groups/:groupId/nested_groups">
          <InventoryRelatedGroupList />
        </Route>,
        { context: { router: { history } } }
      );
    });
    await waitForElement(
      wrapper,
      'InventoryRelatedGroupList',
      (el) => el.length > 0
    );
    act(() => wrapper.find('Button[aria-label="Add"]').prop('onClick')());
    wrapper.update();
    await act(async () =>
      wrapper
        .find('DropdownItem[aria-label="Add existing group"]')
        .prop('onClick')()
    );
    expect(GroupsAPI.readPotentialGroups).toBeCalledWith('2', {
      not__id: '2',
      not__parents: '2',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
    wrapper.update();
    act(() =>
      wrapper.find('CheckboxListItem[name="foo"]').prop('onSelect')({ id: 1 })
    );
    wrapper.update();
    await act(() =>
      wrapper.find('button[aria-label="Save"]').prop('onClick')()
    );
    expect(GroupsAPI.associateChildGroup).toBeCalledTimes(1);
  });

  test('should not render Run Commands button', async () => {
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            module_name: {
              choices: [
                ['command', 'command'],
                ['shell', 'shell'],
              ],
            },
          },
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    expect(wrapper.find('AdHocCommands')).toHaveLength(0);
  });
});

describe('<InventoryRelatedGroupList> for constructed inventories', () => {
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'constructed_inventory',
    }),
  }));
  let wrapper;

  beforeEach(async () => {
    GroupsAPI.readChildren.mockResolvedValue({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [
          'parents__search',
          'inventory__search',
          'inventory_sources__search',
          'created_by__search',
          'children__search',
          'modified_by__search',
          'hosts__search',
        ],
      },
    });
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            module_name: {
              choices: [
                ['command', 'command'],
                ['shell', 'shell'],
              ],
            },
          },
          POST: {},
        },
      },
    });
    const history = createMemoryHistory({
      initialEntries: [
        '/inventories/constructed_inventory/1/groups/2/nested_groupss',
      ],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/groups/:groupId/nested_groups">
          <InventoryRelatedGroupList />
        </Route>,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('Should not show associate, or disassociate button', async () => {
    InventoriesAPI.readHostsOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
      },
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('AddDropDownButton').length).toBe(0);
    expect(wrapper.find('DisassociateButton').length).toBe(0);
  });
});
