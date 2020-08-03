import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryHostList from './SmartInventoryHostList';
import mockInventory from '../shared/data.inventory.json';
import mockHosts from '../shared/data.hosts.json';

jest.mock('../../../api');

describe('<SmartInventoryHostList />', () => {
  describe('User has adhoc permissions', () => {
    let wrapper;
    const clonedInventory = {
      ...mockInventory,
      summary_fields: {
        ...mockInventory.summary_fields,
        user_capabilities: {
          ...mockInventory.summary_fields.user_capabilities,
        },
      },
    };

    beforeAll(async () => {
      InventoriesAPI.readHosts.mockResolvedValue({
        data: mockHosts,
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryHostList inventory={clonedInventory} />
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('initially renders successfully', () => {
      expect(wrapper.find('SmartInventoryHostList').length).toBe(1);
    });

    test('should fetch hosts from api and render them in the list', () => {
      expect(InventoriesAPI.readHosts).toHaveBeenCalled();
      expect(wrapper.find('SmartInventoryHostListItem').length).toBe(3);
    });

    test('should disable run commands button when no hosts are selected', () => {
      wrapper.find('DataListCheck').forEach(el => {
        expect(el.props().checked).toBe(false);
      });
      const runCommandsButton = wrapper.find(
        'button[aria-label="Run commands"]'
      );
      expect(runCommandsButton.length).toBe(1);
      expect(runCommandsButton.prop('disabled')).toEqual(true);
    });

    test('should enable run commands button when at least one host is selected', () => {
      act(() => {
        wrapper.find('DataListCheck[id="select-host-2"]').invoke('onChange')(
          true
        );
      });
      wrapper.update();
      const runCommandsButton = wrapper.find(
        'button[aria-label="Run commands"]'
      );
      expect(runCommandsButton.prop('disabled')).toEqual(false);
    });

    test('should select and deselect all items', async () => {
      act(() => {
        wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
      });
      wrapper.update();
      wrapper.find('DataListCheck').forEach(el => {
        expect(el.props().checked).toEqual(true);
      });
      act(() => {
        wrapper.find('DataListToolbar').invoke('onSelectAll')(false);
      });
      wrapper.update();
      wrapper.find('DataListCheck').forEach(el => {
        expect(el.props().checked).toEqual(false);
      });
    });

    test('should show content error when api throws an error', async () => {
      InventoriesAPI.readHosts.mockImplementation(() =>
        Promise.reject(new Error())
      );
      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryHostList inventory={mockInventory} />
        );
      });
      await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    });
  });

  describe('User does not have adhoc permissions', () => {
    let wrapper;
    const clonedInventory = {
      ...mockInventory,
      summary_fields: {
        user_capabilities: {
          adhoc: false,
        },
      },
    };

    test('should hide run commands button', async () => {
      InventoriesAPI.readHosts.mockResolvedValue({
        data: { results: [], count: 0 },
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryHostList inventory={clonedInventory} />
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
      const runCommandsButton = wrapper.find(
        'button[aria-label="Run commands"]'
      );
      expect(runCommandsButton.length).toBe(0);
      jest.clearAllMocks();
      wrapper.unmount();
    });
  });
});
