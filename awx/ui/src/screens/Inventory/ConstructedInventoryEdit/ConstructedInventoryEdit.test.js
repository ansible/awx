import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { ConstructedInventoriesAPI, InventoriesAPI } from 'api';

import ConstructedInventoryEdit from './ConstructedInventoryEdit';
jest.mock('api');

describe('<ConstructedInventoryEdit />', () => {
  let wrapper;
  let history;

  const mockInv = {
    name: 'Mock',
    id: 7,
    description: 'Foo',
    organization: { id: 1 },
    kind: 'constructed',
    source_vars: 'plugin: constructed',
    limit: 'product_dev',
  };
  const associatedInstanceGroups = [
    {
      id: 1,
      name: 'Foo',
    },
  ];
  const associatedInputInventories = [
    {
      id: 123,
      name: 'input_inventory_123',
    },
    {
      id: 456,
      name: 'input_inventory_456',
    },
  ];
  const mockFormValues = {
    kind: 'constructed',
    name: 'new constructed inventory',
    description: '',
    organization: { id: 1, name: 'mock organization' },
    instanceGroups: associatedInstanceGroups,
    source_vars: 'plugin: constructed',
    inputInventories: associatedInputInventories,
  };

  beforeEach(async () => {
    ConstructedInventoriesAPI.readConstructedInventoryOptions.mockResolvedValue(
      {
        limit: {
          label: 'Limit',
          help_text: '',
        },
        update_cache_timeout: {
          label: 'Update cache timeout',
          help_text: 'help',
        },
        verbosity: {
          label: 'Verbosity',
          help_text: '',
        },
      }
    );
    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: {
        results: associatedInstanceGroups,
      },
    });
    InventoriesAPI.readInputInventories.mockResolvedValue({
      data: {
        results: [
          {
            id: 456,
            name: 'input_inventory_456',
          },
        ],
      },
    });
    history = createMemoryHistory({
      initialEntries: ['/inventories/constructed_inventory/7/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventoryEdit inventory={mockInv} />,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should navigate to inventories details on cancel', async () => {
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/7/edit'
    );
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/7/details'
    );
  });

  test('should navigate to constructed inventory detail after successful submission', async () => {
    ConstructedInventoriesAPI.update.mockResolvedValueOnce({ data: { id: 1 } });
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/7/edit'
    );
    await act(async () => {
      wrapper.find('ConstructedInventoryForm').invoke('onSubmit')(
        mockFormValues
      );
    });
    wrapper.update();
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/7/details'
    );
  });

  test('should make expected api requests on submit', async () => {
    await act(async () => {
      wrapper.find('ConstructedInventoryForm').invoke('onSubmit')(
        mockFormValues
      );
    });
    expect(ConstructedInventoriesAPI.update).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.associateInstanceGroup).not.toHaveBeenCalled();
    expect(InventoriesAPI.disassociateInventory).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.associateInventory).toHaveBeenCalledTimes(2);
    expect(InventoriesAPI.associateInventory).toHaveBeenNthCalledWith(
      1,
      7,
      123
    );
    expect(InventoriesAPI.associateInventory).toHaveBeenNthCalledWith(
      2,
      7,
      456
    );
  });

  test('should throw content error', async () => {
    expect(wrapper.find('ContentError').length).toBe(0);
    InventoriesAPI.readInstanceGroups.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventoryEdit inventory={mockInv} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should throw content error if user has insufficient options permissions', async () => {
    expect(wrapper.find('ContentError').length).toBe(0);
    ConstructedInventoriesAPI.readConstructedInventoryOptions.mockImplementationOnce(
      () => Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventoryEdit inventory={mockInv} />
      );
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('unsuccessful form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    ConstructedInventoriesAPI.update.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventoryEdit inventory={mockInv} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    await act(async () => {
      wrapper.find('ConstructedInventoryForm').invoke('onSubmit')(
        mockFormValues
      );
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
