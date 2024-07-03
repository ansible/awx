import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import '@testing-library/jest-dom';
import { ConstructedInventoriesAPI, InventoriesAPI } from 'api';
import ConstructedInventoryAdd from './ConstructedInventoryAdd';

jest.mock('api');

describe('<ConstructedInventoryAdd />', () => {
  let wrapper;
  let history;

  const formData = {
    name: 'Mock',
    description: 'Foo',
    organization: { id: 1 },
    kind: 'constructed',
    source_vars: 'plugin: constructed',
    inputInventories: [{ id: 2 }],
    instanceGroups: [],
  };

  beforeEach(async () => {
    ConstructedInventoriesAPI.readOptions.mockResolvedValue({
      data: {
        related: {},
        actions: {
          POST: {
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
          },
        },
      },
    });
    history = createMemoryHistory({
      initialEntries: ['/inventories/constructed_inventory/add'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<ConstructedInventoryAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should navigate to inventories list on cancel', async () => {
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/add'
    );
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/inventories');
  });

  test('should navigate to constructed inventory detail after successful submission', async () => {
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    ConstructedInventoriesAPI.create.mockResolvedValueOnce({ data: { id: 1 } });
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/add'
    );
    await act(async () => {
      wrapper.find('ConstructedInventoryForm').invoke('onSubmit')(formData);
    });
    wrapper.update();
    expect(history.location.pathname).toEqual(
      '/inventories/constructed_inventory/1/details'
    );
  });

  test('should make expected api requests on submit', async () => {
    ConstructedInventoriesAPI.create.mockResolvedValueOnce({ data: { id: 1 } });
    await act(async () => {
      wrapper.find('ConstructedInventoryForm').invoke('onSubmit')(formData);
    });
    expect(ConstructedInventoriesAPI.create).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.associateInventory).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.associateInventory).toHaveBeenCalledWith(1, 2);
    expect(InventoriesAPI.associateInstanceGroup).not.toHaveBeenCalled();
  });

  test('unsuccessful form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    ConstructedInventoriesAPI.create.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper = mountWithContexts(<ConstructedInventoryAdd />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    await act(async () => {
      wrapper.find('ConstructedInventoryForm').invoke('onSubmit')(formData);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
