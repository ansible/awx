import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { InventoriesAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import InventoryLookup from './InventoryLookup';

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
      wrapper = mountWithContexts(
        <Formik>
          <InventoryLookup onChange={() => {}} />
        </Formik>
      );
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.read).toHaveBeenCalledWith({
      order_by: 'name',
      page: 1,
      page_size: 5,
      role_level: 'use_role',
    });
    expect(wrapper.find('InventoryLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(false);
  });

  test('should fetch only regular inventories when hideSmartInventories is true', async () => {
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
      wrapper = mountWithContexts(
        <Formik>
          <InventoryLookup onChange={() => {}} hideSmartInventories />
        </Formik>
      );
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.read).toHaveBeenCalledWith({
      not__kind: 'smart',
      order_by: 'name',
      page: 1,
      page_size: 5,
      role_level: 'use_role',
    });
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
        <Formik>
          <InventoryLookup onChange={() => {}} />
        </Formik>
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
      wrapper = mountWithContexts(
        <Formik>
          <InventoryLookup isDisabled onChange={() => {}} />
        </Formik>
      );
    });
    wrapper.update();
    expect(InventoriesAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('InventoryLookup')).toHaveLength(1);
    expect(wrapper.find('Lookup').prop('isDisabled')).toBe(true);
  });
});
