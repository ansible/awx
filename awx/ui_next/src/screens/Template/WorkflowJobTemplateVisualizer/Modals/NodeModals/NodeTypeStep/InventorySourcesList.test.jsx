import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';
import { InventorySourcesAPI } from '../../../../../../api';
import InventorySourcesList from './InventorySourcesList';

jest.mock('../../../../../../api/models/InventorySources');

const nodeResource = {
  id: 1,
  name: 'Test Inventory Source',
  unified_job_type: 'workflow_approval',
};
const onUpdateNodeResource = jest.fn();

describe('InventorySourcesList', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('Row selected when nodeResource id matches row id and clicking new row makes expected callback', async () => {
    InventorySourcesAPI.read.mockResolvedValueOnce({
      data: {
        count: 2,
        results: [
          {
            id: 1,
            name: 'Test Inventory Source',
            type: 'inventory_source',
            url: '/api/v2/inventory_sources/1',
          },
          {
            id: 2,
            name: 'Test Inventory Source 2',
            type: 'inventory_source',
            url: '/api/v2/inventory_sources/2',
          },
        ],
      },
    });
    InventorySourcesAPI.readOptions.mockResolvedValue({
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
        <InventorySourcesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper.find('CheckboxListItem[name="Test Inventory Source"]').props()
        .isSelected
    ).toBe(true);
    expect(
      wrapper.find('CheckboxListItem[name="Test Inventory Source 2"]').props()
        .isSelected
    ).toBe(false);
    wrapper
      .find('CheckboxListItem[name="Test Inventory Source 2"]')
      .simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 2,
      name: 'Test Inventory Source 2',
      type: 'inventory_source',
      url: '/api/v2/inventory_sources/2',
    });
  });
  test('Error shown when read() request errors', async () => {
    InventorySourcesAPI.read.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourcesList
          nodeResource={nodeResource}
          onUpdateNodeResource={onUpdateNodeResource}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
