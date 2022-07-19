import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  InventorySourcesAPI,
  InventoriesAPI,
  WorkflowJobTemplateNodesAPI,
} from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventorySourceDetail from './InventorySourceDetail';
import mockInvSource from '../shared/data.inventory_source.json';

jest.mock('../../../api');

function assertDetail(wrapper, label, value) {
  expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
  expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
}

describe('InventorySourceDetail', () => {
  let wrapper;

  beforeEach(async () => {
    InventoriesAPI.updateSources.mockResolvedValue({
      data: [{ inventory_source: 1 }],
    });
    WorkflowJobTemplateNodesAPI.read.mockResolvedValue({ data: { count: 0 } });
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
                ['controller', 'Red Hat Ansible Automation Platform'],
              ],
            },
          },
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render cancel button while job is running', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail
          inventorySource={{
            ...mockInvSource,
            summary_fields: {
              ...mockInvSource.summary_fields,
              current_job: {
                id: 42,
                status: 'running',
              },
            },
          }}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('InventorySourceDetail')).toHaveLength(1);

    expect(wrapper.find('JobCancelButton').length).toBe(1);
  });

  test('should render expected details', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('InventorySourceDetail')).toHaveLength(1);
    assertDetail(wrapper, 'Name', 'mock inv source');
    assertDetail(wrapper, 'Description', 'mock description');
    assertDetail(wrapper, 'Source', 'Sourced from a Project');
    assertDetail(wrapper, 'Organization', 'Mock Org');
    assertDetail(wrapper, 'Project', 'Mock Project');
    assertDetail(wrapper, 'Inventory file', 'foo');
    assertDetail(wrapper, 'Verbosity', '2 (More Verbose)');
    assertDetail(wrapper, 'Cache timeout', '2 seconds');
    const executionEnvironment = wrapper.find('ExecutionEnvironmentDetail');
    expect(executionEnvironment).toHaveLength(1);
    expect(executionEnvironment.find('dt').text()).toEqual(
      'Execution Environment'
    );
    expect(executionEnvironment.find('dd').text()).toEqual(
      mockInvSource.summary_fields.execution_environment.name
    );

    expect(wrapper.find('CredentialChip').text()).toBe('Cloud: mock cred');
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---\nfoo: bar'
    );
    wrapper.find('Detail[label="Enabled Options"] li').forEach((option) => {
      expect([
        'Overwrite local groups and hosts from remote inventory source',
        'Overwrite local variables from remote inventory source',
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    const editButton = wrapper.find('Button[aria-label="edit"]');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe(
      '/inventories/inventory/2/sources/123/edit'
    );
    expect(wrapper.find('DeleteButton')).toHaveLength(1);
    expect(wrapper.find('InventorySourceSyncButton')).toHaveLength(1);
  });

  test('should have proper number of delete detail requests', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail inventorySource={mockInvSource} />
      );
    });
    expect(
      wrapper.find('DeleteButton').prop('deleteDetailsRequests')
    ).toHaveLength(3);
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
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
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('Modal[title="Error!"]')).toHaveLength(0);
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 0
    );
  });

  test('should not load Credentials', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventorySourceDetail
          inventorySource={{
            ...mockInvSource,
            summary_fields: {
              credentials: [],
            },
          }}
        />
      );
    });
    const credentials_detail = wrapper.find(`Detail[label="Credential"]`).at(0);
    expect(credentials_detail.prop('isEmpty')).toEqual(true);
  });
});
