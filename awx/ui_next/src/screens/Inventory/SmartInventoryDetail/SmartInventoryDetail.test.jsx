import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryDetail from './SmartInventoryDetail';
import { InventoriesAPI, UnifiedJobsAPI } from '../../../api';

import mockSmartInventory from '../shared/data.smart_inventory.json';

jest.mock('../../../api/models/UnifiedJobs');
jest.mock('../../../api/models/Inventories');

UnifiedJobsAPI.read.mockResolvedValue({
  data: {
    results: [
      {
        id: 1,
        name: 'job 1',
        type: 'job',
        status: 'successful',
      },
    ],
  },
});
InventoriesAPI.readInstanceGroups.mockResolvedValue({
  data: {
    results: [{ id: 1, name: 'mock instance group' }],
  },
});

describe('<SmartInventoryDetail />', () => {
  let wrapper;

  describe('User has edit permissions', () => {
    beforeAll(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryDetail inventory={mockSmartInventory} />
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      wrapper.unmount();
      jest.clearAllMocks();
    });

    test('should render Details', async () => {
      function assertDetail(label, value) {
        expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
        expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
      }

      assertDetail('Name', 'Smart Inv');
      assertDetail('Description', 'smart inv description');
      assertDetail('Type', 'Smart inventory');
      assertDetail('Organization', 'Default');
      assertDetail('Smart host filter', 'name__icontains=local');
      assertDetail('Instance groups', 'mock instance group');
      expect(wrapper.find(`Detail[label="Activity"] Sparkline`)).toHaveLength(
        1
      );
      const vars = wrapper.find('VariablesDetail');
      expect(vars).toHaveLength(1);
      expect(vars.prop('value')).toEqual(mockSmartInventory.variables);
      const dates = wrapper.find('UserDateDetail');
      expect(dates).toHaveLength(2);
      expect(dates.at(0).prop('date')).toEqual(mockSmartInventory.created);
      expect(dates.at(1).prop('date')).toEqual(mockSmartInventory.modified);
    });

    test('should show edit button for users with edit permission', () => {
      const editButton = wrapper.find('Button[aria-label="edit"]');
      expect(editButton.text()).toEqual('Edit');
      expect(editButton.prop('to')).toBe(
        `/inventories/smart_inventory/${mockSmartInventory.id}/edit`
      );
    });

    test('expected api calls are made on initial render', () => {
      expect(InventoriesAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
      expect(UnifiedJobsAPI.read).toHaveBeenCalledTimes(1);
    });

    test('expected api call is made for delete', async () => {
      expect(InventoriesAPI.destroy).toHaveBeenCalledTimes(0);
      await act(async () => {
        wrapper.find('DeleteButton').invoke('onConfirm')();
      });
      expect(InventoriesAPI.destroy).toHaveBeenCalledTimes(1);
    });

    test('Error dialog shown for failed deletion', async () => {
      InventoriesAPI.destroy.mockImplementationOnce(() =>
        Promise.reject(new Error())
      );
      await act(async () => {
        wrapper.find('DeleteButton').invoke('onConfirm')();
      });
      await waitForElement(
        wrapper,
        'Modal[title="Error!"]',
        el => el.length === 1
      );
      await act(async () => {
        wrapper.find('Modal[title="Error!"]').invoke('onClose')();
      });
      await waitForElement(
        wrapper,
        'Modal[title="Error!"]',
        el => el.length === 0
      );
    });
  });

  describe('User has read-only permissions', () => {
    afterEach(() => {
      wrapper.unmount();
      jest.clearAllMocks();
    });

    test('should hide edit button for users without edit permission', async () => {
      const readOnlySmartInv = { ...mockSmartInventory };
      readOnlySmartInv.summary_fields.user_capabilities.edit = false;

      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryDetail inventory={readOnlySmartInv} />
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
      expect(wrapper.find('Button[aria-label="edit"]').length).toBe(0);
    });

    test('should show content error when jobs request fails', async () => {
      UnifiedJobsAPI.read.mockImplementationOnce(() =>
        Promise.reject(new Error())
      );
      expect(UnifiedJobsAPI.read).toHaveBeenCalledTimes(0);
      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryDetail inventory={mockSmartInventory} />
        );
      });
      expect(UnifiedJobsAPI.read).toHaveBeenCalledTimes(1);
      await waitForElement(wrapper, 'ContentError', el => el.length === 1);
      expect(wrapper.find('ContentError Title').text()).toEqual(
        'Something went wrong...'
      );
    });
  });
});
