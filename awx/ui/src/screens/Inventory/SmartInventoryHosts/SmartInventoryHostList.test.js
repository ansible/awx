import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryHostList from './SmartInventoryHostList';
import mockInventory from '../shared/data.inventory.json';
import mockHosts from '../shared/data.hosts.json';

jest.mock('../../../api');

describe('<SmartInventoryHostList />', () => {
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

  beforeEach(async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: mockHosts,
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
      wrapper = mountWithContexts(
        <SmartInventoryHostList inventory={clonedInventory} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('SmartInventoryHostList').length).toBe(1);
  });

  test('should fetch hosts from api and render them in the list', () => {
    expect(InventoriesAPI.readHosts).toHaveBeenCalled();
    expect(wrapper.find('SmartInventoryHostListItem').length).toBe(3);
  });

  test('should select and deselect all items', async () => {
    expect.assertions(6);
    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();
    wrapper.find('.pf-c-table__check input').forEach((el) => {
      expect(el.props().checked).toEqual(true);
    });
    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(false);
    });
    wrapper.update();
    wrapper.find('.pf-c-table__check input').forEach((el) => {
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
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
