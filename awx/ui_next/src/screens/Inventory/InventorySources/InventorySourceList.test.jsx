import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI, InventorySourcesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InventorySourceList from './InventorySourceList';

jest.mock('../../../api/models/InventorySources');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/InventoryUpdates');

const sources = {
  data: {
    results: [
      {
        id: 1,
        name: 'Source Foo',
        status: '',
        source: 'ec2',
        url: '/api/v2/inventory_sources/56/',
        summary_fields: {
          user_capabilities: {
            edit: true,
            delete: true,
            start: true,
            schedule: true,
          },
        },
      },
      {
        id: 2,
        name: 'Source Bar',
        status: '',
        source: 'scm',
        url: '/api/v2/inventory_sources/57/',
        summary_fields: {
          user_capabilities: {
            edit: true,
            delete: true,
            start: true,
            schedule: true,
          },
        },
      },
    ],
    count: 1,
  },
};

describe('<InventorySourceList />', () => {
  let wrapper;
  let history;
  let debug;

  beforeEach(async () => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
    InventoriesAPI.readSources.mockResolvedValue(sources);
    InventorySourcesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            source: {
              choices: [
                ['scm', 'SCM'],
                ['ec2', 'EC2'],
              ],
            },
          },
          POST: {},
        },
      },
    });
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/sources'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/sources">
          <InventorySourceList />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: { search: '' },
                match: { params: { id: 1 } },
              },
            },
          },
        }
      );
    });
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
    global.console.debug = debug;
  });

  test('should mount properly', async () => {
    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);
  });

  test('api calls should be made on mount', async () => {
    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);
    expect(InventoriesAPI.readSources).toHaveBeenCalledWith('1', {
      not__source: '',
      order_by: 'name',
      page: 1,
      page_size: 20,
    });
    expect(InventorySourcesAPI.readOptions).toHaveBeenCalled();
  });

  test('source data should render properly', async () => {
    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);
    expect(
      wrapper
        .find("DataListItem[aria-labelledby='check-action-1']")
        .find('PFDataListCell[aria-label="name"]')
        .text()
    ).toBe('Source Foo');
    expect(
      wrapper
        .find("DataListItem[aria-labelledby='check-action-1']")
        .find('PFDataListCell[aria-label="type"]')
        .text()
    ).toBe('EC2');
  });

  test('add button is not disabled and delete button is disabled', async () => {
    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);
    const addButton = wrapper.find('ToolbarAddButton').find('Link');
    const deleteButton = wrapper.find('ToolbarDeleteButton').find('Button');
    expect(addButton.prop('aria-disabled')).toBe(false);
    expect(deleteButton.prop('isDisabled')).toBe(true);
  });

  test('delete button becomes enabled and properly calls api to delete', async () => {
    const deleteButton = wrapper.find('ToolbarDeleteButton').find('Button');

    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);
    expect(deleteButton.prop('isDisabled')).toBe(true);

    await act(async () =>
      wrapper.find('DataListCheck#select-source-1').prop('onChange')({ id: 1 })
    );
    wrapper.update();
    expect(wrapper.find('input#select-source-1').prop('checked')).toBe(true);

    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    expect(InventorySourcesAPI.destroy).toHaveBeenCalledWith(1);
    expect(InventorySourcesAPI.destroyHosts).toHaveBeenCalledWith(1);
    expect(InventorySourcesAPI.destroyGroups).toHaveBeenCalledWith(1);
  });

  test('should throw error after deletion failure', async () => {
    InventorySourcesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/inventory_sources/',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);

    await act(async () =>
      wrapper.find('DataListCheck#select-source-1').prop('onChange')({ id: 1 })
    );
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find("AlertModal[aria-label='Delete error']").length).toBe(
      1
    );
  });

  test('displays error after unsuccessful read sources fetch', async () => {
    InventorySourcesAPI.readOptions.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/inventories/inventory_sources/',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    InventoriesAPI.readSources.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2/inventories/inventory_sources/',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceList />);
    });

    await waitForElement(wrapper, 'ContentError', el => el.length > 0);

    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('displays error after unsuccessful read options fetch', async () => {
    InventorySourcesAPI.readOptions.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'options',
            url: '/api/v2/inventory_sources/',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await act(async () => {
      wrapper = mountWithContexts(<InventorySourceList />);
    });

    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);

    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('displays error after unsuccessful sync all button', async () => {
    InventoriesAPI.syncAllSources.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/inventories/',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    await waitForElement(wrapper, 'InventorySourceList', el => el.length > 0);
    await act(async () =>
      wrapper.find('Button[aria-label="Sync all"]').prop('onClick')()
    );
    expect(InventoriesAPI.syncAllSources).toBeCalled();
    wrapper.update();
    expect(wrapper.find("AlertModal[aria-label='Sync error']").length).toBe(1);
  });

  test('should render sync all button and make api call to start sync for all', async () => {
    await waitForElement(
      wrapper,
      'InventorySourceListItem',
      el => el.length > 0
    );
    const syncAllButton = wrapper.find('Button[aria-label="Sync all"]');
    expect(syncAllButton.length).toBe(1);
    await act(async () => syncAllButton.prop('onClick')());
    expect(InventoriesAPI.syncAllSources).toBeCalled();
    expect(InventoriesAPI.readSources).toBeCalled();
  });
});

describe('<InventorySourceList /> RBAC testing', () => {
  test('should not render add button', async () => {
    sources.data.results[0].summary_fields.user_capabilities = {
      edit: true,
      delete: true,
      start: true,
      schedule: true,
    };
    InventoriesAPI.readSources.mockResolvedValue(sources);
    InventorySourcesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {
            source: {
              choices: [
                ['scm', 'SCM'],
                ['ec2', 'EC2'],
              ],
            },
          },
        },
      },
    });
    let newWrapper;
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/2/sources'],
    });
    await act(async () => {
      newWrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/sources">
          <InventorySourceList />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: { search: '' },
                match: { params: { id: 2 } },
              },
            },
          },
        }
      );
    });
    await waitForElement(
      newWrapper,
      'InventorySourceList',
      el => el.length > 0
    );
    expect(newWrapper.find('ToolbarAddButton').length).toBe(0);
    newWrapper.unmount();
    jest.clearAllMocks();
  });

  test('should not render Sync All button', async () => {
    sources.data.results[0].summary_fields.user_capabilities = {
      edit: true,
      delete: true,
      start: false,
      schedule: true,
    };
    InventoriesAPI.readSources.mockResolvedValue(sources);
    let newWrapper;
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/2/sources'],
    });
    await act(async () => {
      newWrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/sources">
          <InventorySourceList />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: { search: '' },
                match: { params: { id: 2 } },
              },
            },
          },
        }
      );
    });
    await waitForElement(
      newWrapper,
      'InventorySourceList',
      el => el.length > 0
    );
    expect(newWrapper.find('Button[aria-label="Sync All"]').length).toBe(0);
    newWrapper.unmount();
    jest.clearAllMocks();
  });
});
