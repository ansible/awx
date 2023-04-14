import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { InventoriesAPI, GroupsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryGroupsList from './InventoryGroupsList';

jest.mock('../../../api');
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

describe('<InventoryGroupsList />', () => {
  let wrapper;
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'inventory',
    }),
  }));
  beforeEach(async () => {
    InventoriesAPI.readGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
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
      initialEntries: ['/inventories/inventory/3/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/groups">
          <InventoryGroupsList />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should fetch groups from api and render them in the list', async () => {
    expect(InventoriesAPI.readGroups).toHaveBeenCalled();
    expect(wrapper.find('InventoryGroupItem').length).toBe(3);
  });

  test('should render Run Commands button', async () => {
    expect(wrapper.find('AdHocCommands')).toHaveLength(1);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('.pf-c-table__check').first().find('input').props().checked
    ).toBe(false);

    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')(true);
    });
    wrapper.update();
    expect(
      wrapper.find('.pf-c-table__check').first().find('input').props().checked
    ).toBe(true);

    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')(false);
    });
    wrapper.update();
    expect(
      wrapper.find('.pf-c-table__check').first().find('input').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    expect.assertions(9);
    wrapper.find('.pf-c-table__check').forEach((el) => {
      expect(el.find('input').props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('.pf-c-table__check').forEach((el) => {
      expect(el.find('input').props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('.pf-c-table__check').forEach((el) => {
      expect(el.find('input').props().checked).toBe(false);
    });
  });

  test('should not render ad hoc commands button', async () => {
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
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    expect(wrapper.find('AdHocCommands')).toHaveLength(0);
  });
});

describe('<InventoryGroupsList/> error handling', () => {
  let wrapper;

  beforeEach(() => {
    InventoriesAPI.readGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
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
    GroupsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/groups/1',
          },
          data: 'An error occurred',
        },
      })
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readGroupsOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length > 0);
  });

  test('should show content error if groups are not successfully fetched from api', async () => {
    InventoriesAPI.readGroups.mockImplementation(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length > 0);
  });

  test('should show error modal when group is not successfully deleted from api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    waitForElement(wrapper, 'ContentEmpty', (el) => el.length === 0);

    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Toolbar Button[aria-label="Delete"]').invoke('onClick')();
    });
    wrapper.update();

    await waitForElement(
      wrapper,
      'AlertModal__Header',
      (el) => el.text() === 'Delete Group?'
    );
    await act(async () => {
      wrapper.find('Radio[id="radio-delete"]').invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('ModalBoxFooter Button[aria-label="Confirm Delete"]')
        .invoke('onClick')();
    });
    await waitForElement(
      wrapper,
      'AlertModal[aria-label="deletion error"] Modal',
      (el) => el.props().isOpen === true && el.props().title === 'Error!'
    );

    await act(async () => {
      wrapper
        .find('AlertModal[aria-label="deletion error"]')
        .invoke('onClose')();
    });
  });
});

describe('Constructed Inventory group', () => {
  let wrapper;
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'constructed_inventory',
    }),
  }));

  beforeEach(async () => {
    InventoriesAPI.readGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
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
      initialEntries: ['/inventories/constructed_inventory/3/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/groups">
          <InventoryGroupsList />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });
  test('should not show add button', () => {
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    expect(wrapper.find('ToolbarDeleteButton').length).toBe(0);
    expect(wrapper.find('AdHocCommands').length).toBe(1);
  });
});
