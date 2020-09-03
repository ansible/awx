import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryStep from './InventoryStep';
import { InventoriesAPI } from '../../../api';

jest.mock('../../../api/models/Inventories');

const inventories = [
  { id: 1, name: 'inv one', url: '/inventories/1' },
  { id: 2, name: 'inv two', url: '/inventories/2' },
  { id: 3, name: 'inv three', url: '/inventories/3' },
];

describe('InventoryStep', () => {
  beforeEach(() => {
    InventoriesAPI.read.mockResolvedValue({
      data: {
        results: inventories,
        count: 3,
      },
    });

    InventoriesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  test('should load inventories', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <InventoryStep />
        </Formik>
      );
    });
    wrapper.update();

    expect(InventoriesAPI.read).toHaveBeenCalled();
    expect(wrapper.find('OptionsList').prop('options')).toEqual(inventories);
  });
});
