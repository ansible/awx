import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI, CredentialTypesAPI } from '../../../api';
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

  beforeAll(async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: mockHosts,
    });
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: { module_name: { choices: [['module']] } },
          POST: {},
        },
      },
    });
    CredentialTypesAPI.read.mockResolvedValue({
      data: { count: 1, results: [{ id: 1, name: 'cred' }] },
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

  test('should have run command button', () => {
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
    const runCommandsButton = wrapper.find('button[aria-label="Run command"]');
    expect(runCommandsButton.length).toBe(1);
    expect(runCommandsButton.prop('disabled')).toBe(false);
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
  test('should disable run commands button', async () => {
    InventoriesAPI.readHosts.mockResolvedValue({
      data: { results: [], count: 0 },
    });
    InventoriesAPI.readAdHocOptions.mockResolvedValue({
      data: {
        actions: {
          GET: { module_name: { choices: [['module']] } },
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryHostList inventory={clonedInventory} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const runCommandsButton = wrapper.find('button[aria-label="Run command"]');
    expect(runCommandsButton.prop('disabled')).toBe(true);
  });
});
