import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventorySourceDetail from './InventorySourceDetail';
import mockInvSource from '../shared/data.inventory_source.json';
import { InventorySourcesAPI } from '../../../api';

jest.mock('../../../api/models/InventorySources');
InventorySourcesAPI.readOptions.mockResolvedValue({
  data: {
    actions: {
      GET: {
        source: {
          choices: [
            ['file', 'File, Directory or Script'],
            ['scm', 'Sourced from a Project'],
            ['ec2', 'Amazon EC2'],
            ['gce', 'Google Compute Engine'],
            ['azure_rm', 'Microsoft Azure Resource Manager'],
            ['vmware', 'VMware vCenter'],
            ['satellite6', 'Red Hat Satellite 6'],
            ['openstack', 'OpenStack'],
            ['rhv', 'Red Hat Virtualization'],
            ['tower', 'Ansible Tower'],
          ],
        },
      },
    },
  },
});

function assertDetail(wrapper, label, value) {
  expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
  expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
}

describe('InventorySourceDetail', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render expected details', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('InventorySourceDetail')).toHaveLength(1);
    assertDetail(wrapper, 'Name', 'mock inv source');
    assertDetail(wrapper, 'Description', 'mock description');
    assertDetail(wrapper, 'Source', 'Sourced from a Project');
    assertDetail(wrapper, 'Organization', 'Mock Org');
    assertDetail(wrapper, 'Ansible environment', '/venv/custom');
    assertDetail(wrapper, 'Project', 'Mock Project');
    assertDetail(wrapper, 'Inventory file', 'foo');
    assertDetail(wrapper, 'Verbosity', '2 (Debug)');
    assertDetail(wrapper, 'Cache timeout', '2 seconds');
    expect(wrapper.find('CredentialChip').text()).toBe('Cloud: mock cred');
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---\nfoo: bar'
    );
    wrapper.find('Detail[label="Options"] li').forEach(option => {
      expect([
        'Overwrite',
        'Overwrite variables',
        'Update on launch',
        'Update on project update',
      ]).toContain(option.text());
    });
  });

  test('should display expected action buttons for users with permissions', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    const editButton = wrapper.find('Button[aria-label="edit"]');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe(
      '/inventories/inventory/2/sources/123/edit'
    );
    expect(wrapper.find('DeleteButton')).toHaveLength(1);
    expect(wrapper.find('InventorySourceSyncButton')).toHaveLength(1);
  });

  test('should hide expected action buttons for users without permissions', async () => {
    const userCapabilities = {
      edit: false,
      delete: false,
      start: false,
    };
    const invSource = {
      ...mockInvSource,
      summary_fields: { ...userCapabilities },
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={invSource} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="edit"]')).toHaveLength(0);
    expect(wrapper.find('DeleteButton')).toHaveLength(0);
    expect(wrapper.find('InventorySourceSyncButton')).toHaveLength(0);
  });

  test('expected api call is made for delete', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/2/sources/123/details'],
    });
    act(() => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />,
        {
          context: { router: { history } },
        }
      );
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/2/sources/123/details'
    );
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(InventorySourcesAPI.destroy).toHaveBeenCalledTimes(1);
    expect(InventorySourcesAPI.destroyHosts).toHaveBeenCalledTimes(1);
    expect(InventorySourcesAPI.destroyGroups).toHaveBeenCalledTimes(1);
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/2/sources'
    );
  });

  test('Content error shown for failed options request', async () => {
    InventorySourcesAPI.readOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    expect(InventorySourcesAPI.readOptions).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />
      );
    });
    expect(InventorySourcesAPI.readOptions).toHaveBeenCalledTimes(1);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    expect(wrapper.find('ContentError Title').text()).toEqual(
      'Something went wrong...'
    );
  });

  test('Error dialog shown for failed deletion', async () => {
    InventorySourcesAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Modal[title="Error!"]')).toHaveLength(0);
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
