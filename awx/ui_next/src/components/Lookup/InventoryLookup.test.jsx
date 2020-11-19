import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import InventoryLookup from './InventoryLookup';
import { InventoriesAPI } from '../../api';

jest.mock('../../api');

const mockedInventories = {
  data: {
    count: 2,
    results: [
      { id: 2, name: 'Bar' },
      { id: 3, name: 'Baz' },
    ],
  },
};

describe('InventoryLookup', () => {
  let wrapper;

  beforeEach(() => {
    InventoriesAPI.read.mockResolvedValue(mockedInventories);
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should render successfully and fetch data', async () => {
    InventoriesAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryLookup onChange={() => {}} />);
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('InventoryLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(false);
  });

  test('inventory lookup should be enabled', async () => {
    InventoriesAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryLookup isOverrideDisabled onChange={() => {}} />
      );
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('InventoryLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(false);
  });

  test('inventory lookup should be disabled', async () => {
    InventoriesAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryLookup onChange={() => {}} />);
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('InventoryLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(true);
  });
});
