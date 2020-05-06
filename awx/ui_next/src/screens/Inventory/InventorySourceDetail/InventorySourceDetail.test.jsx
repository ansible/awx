import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '../../../../testUtils/enzymeHelpers';
import InventorySourceDetail from './InventorySourceDetail';
import mockInvSource from '../shared/data.inventory_source.json';
import { InventorySourcesAPI } from '../../../api';

jest.mock('../../../api/models/InventorySources');

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

  test('should render expected details', () => {
    wrapper = mountWithContexts(
      <InventorySourceDetail inventorySource={mockInvSource} />
    );
    expect(wrapper.find('InventorySourceDetail')).toHaveLength(1);
    assertDetail(wrapper, 'Name', 'mock inv source');
    assertDetail(wrapper, 'Description', 'mock description');
    assertDetail(wrapper, 'Source', 'scm');
    assertDetail(wrapper, 'Organization', 'Mock Org');
    assertDetail(wrapper, 'Ansible environment', '/venv/custom');
    assertDetail(wrapper, 'Project', 'Mock Project');
    assertDetail(wrapper, 'Inventory file', 'foo');
    assertDetail(wrapper, 'Custom inventory script', 'Mock Script');
    assertDetail(wrapper, 'Verbosity', '2 (Debug)');
    assertDetail(wrapper, 'Cache timeout', '2 seconds');
    expect(
      wrapper
        .find('Detail[label="Regions"]')
        .containsAllMatchingElements([
          <span>us-east-1</span>,
          <span>us-east-2</span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Instance filters"]')
        .containsAllMatchingElements([
          <span>filter1</span>,
          <span>filter2</span>,
          <span>filter3</span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Only group by"]')
        .containsAllMatchingElements([
          <span>group1</span>,
          <span>group2</span>,
          <span>group3</span>,
        ])
    ).toEqual(true);
    expect(wrapper.find('CredentialChip').text()).toBe('Cloud: mock cred');
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---\nfoo: bar'
    );
    expect(
      wrapper
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Overwrite</li>,
          <li>Overwrite variables</li>,
          <li>Update on launch</li>,
          <li>Update on project update</li>,
        ])
    ).toEqual(true);
  });

  test('should show edit and delete button for users with permissions', () => {
    wrapper = mountWithContexts(
      <InventorySourceDetail inventorySource={mockInvSource} />
    );
    const editButton = wrapper.find('Button[aria-label="edit"]');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe(
      '/inventories/inventory/2/source/123/edit'
    );
    expect(wrapper.find('DeleteButton')).toHaveLength(1);
  });

  test('should hide edit and delete button for users without permissions', () => {
    const userCapabilities = {
      edit: false,
      delete: false,
    };
    const invSource = {
      ...mockInvSource,
      summary_fields: { ...userCapabilities },
    };
    wrapper = mountWithContexts(
      <InventorySourceDetail inventorySource={invSource} />
    );
    expect(wrapper.find('Button[aria-label="edit"]')).toHaveLength(0);
    expect(wrapper.find('DeleteButton')).toHaveLength(0);
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

  test('Error dialog shown for failed deletion', async () => {
    InventorySourcesAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    wrapper = mountWithContexts(
      <InventorySourceDetail inventorySource={mockInvSource} />
    );
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
