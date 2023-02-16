import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI, HostsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryHostList from './InventoryHostList';
import mockInventory from '../shared/data.inventory.json';

jest.mock('../../../api');

const mockHosts = [
  {
    id: 1,
    name: 'Host 1',
    url: '/api/v2/hosts/1',
    inventory: 1,
    enabled: true,
    summary_fields: {
      inventory: {
        id: 1,
        name: 'inv 1',
      },
      user_capabilities: {
        delete: true,
        update: true,
      },
      recent_jobs: [],
    },
  },
  {
    id: 2,
    name: 'Host 2',
    url: '/api/v2/hosts/2',
    inventory: 1,
    enabled: true,
    summary_fields: {
      inventory: {
        id: 1,
        name: 'inv 1',
      },
      user_capabilities: {
        edit: true,
        delete: true,
        update: true,
      },
      recent_jobs: [],
    },
  },
  {
    id: 3,
    name: 'Host 3',
    url: '/api/v2/hosts/3',
    inventory: 1,
    enabled: true,
    summary_fields: {
      inventory: {
        id: 1,
        name: 'inv 1',
      },
      user_capabilities: {
        delete: false,
        update: false,
      },
      recent_jobs: [
        {
          id: 123,
          name: 'Recent Job',
          status: 'success',
          finished: '2020-01-27T19:40:36.208728Z',
        },
      ],
    },
  },
];

describe('<InventoryHostList />', () => {
  let wrapper;

  beforeEach(async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: {
        count: mockHosts.length,
        results: mockHosts,
      },
    });
    InventoriesAPI.readHostsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: ['first_key__search', 'ansible_facts'],
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
      wrapper = mountWithContexts(<InventoryHostList />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should fetch hosts from api and render them in the list', async () => {
    expect(InventoriesAPI.readHosts).toHaveBeenCalled();
    expect(wrapper.find('InventoryHostItem').length).toBe(3);
    expect(
      wrapper.find('PaginatedTable').props().toolbarRelatedSearchableKeys
    ).toStrictEqual(['first_key', 'ansible_facts']);
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

  test('should call api if host toggle is clicked', async () => {
    HostsAPI.update.mockResolvedValueOnce({
      data: { ...mockHosts[1], enabled: false },
    });
    expect(wrapper.find('Switch[id="host-2-toggle"]').props().isChecked).toBe(
      true
    );
    await act(async () => {
      wrapper.find('Switch[id="host-2-toggle"]').invoke('onChange')();
    });
    wrapper.update();
    expect(wrapper.find('Switch[id="host-2-toggle"]').props().isChecked).toBe(
      false
    );
    expect(HostsAPI.update).toHaveBeenCalledTimes(1);
  });

  test('should show error modal if host is not successfully toggled', async () => {
    HostsAPI.update.mockImplementationOnce(() => Promise.reject(new Error()));
    await act(async () => {
      wrapper.find('Switch[id="host-2-toggle"]').invoke('onChange')();
    });
    wrapper.update();
    await waitForElement(
      wrapper,
      'Modal',
      (el) => el.props().isOpen === true && el.props().title === 'Error!'
    );
    await act(async () => {
      wrapper.find('ModalBoxCloseButton').invoke('onClose')();
    });
    await waitForElement(wrapper, 'Modal', (el) => el.length === 0);
  });

  test('delete button is disabled if user does not have delete capabilities on a selected host', async () => {
    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .at(2)
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    expect(wrapper.find('ToolbarDeleteButton button').props().disabled).toBe(
      true
    );
  });

  test('should call api delete hosts for each selected host', async () => {
    HostsAPI.destroy = jest.fn();
    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();
    expect(HostsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show error modal when host is not successfully deleted from api', async () => {
    HostsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/hosts/1',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    await waitForElement(
      wrapper,
      'Modal',
      (el) => el.props().isOpen === true && el.props().title === 'Error!'
    );
    await act(async () => {
      wrapper.find('ModalBoxCloseButton').invoke('onClose')();
    });
    await waitForElement(wrapper, 'Modal', (el) => el.length === 0);
  });

  test('should show content error if hosts are not successfully fetched from api', async () => {
    InventoriesAPI.readHosts.mockImplementation(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });

  test('should show Add button for users with ability to POST', async () => {
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('should hide Add button for users without ability to POST', async () => {
    InventoriesAPI.readHostsOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHostList inventory={mockInventory} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });

  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readHostsOptions.mockImplementation(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHostList inventory={mockInventory} />
      );
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
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
      wrapper = mountWithContexts(
        <InventoryHostList inventory={mockInventory} />
      );
    });
    expect(wrapper.find('AdHocCommands')).toHaveLength(0);
  });
});

describe('Should not show add button for constructed inventory host list', () => {
  let wrapper;
  let history;
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'constructed_inventory',
    }),
  }));

  beforeEach(async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: {
        count: mockHosts.length,
        results: mockHosts,
      },
    });
    InventoriesAPI.readHostsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: ['first_key__search', 'ansible_facts'],
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
    history = createMemoryHistory({
      initialEntries: ['/inventories/constructed_inventory/3/hosts'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/hosts">
          <InventoryHostList />
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
