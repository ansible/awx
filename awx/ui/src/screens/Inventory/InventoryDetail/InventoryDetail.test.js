import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventoriesAPI, CredentialTypesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryDetail from './InventoryDetail';

jest.mock('../../../api');

const mockInventory = {
  id: 1,
  type: 'inventory',
  url: '/api/v2/inventories/1/',
  summary_fields: {
    organization: {
      id: 1,
      name: 'The Organization',
      description: '',
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      adhoc: true,
    },
  },
  created: '2019-10-04T16:56:48.025455Z',
  modified: '2019-10-04T16:56:48.025468Z',
  name: 'Inv no hosts',
  description: '',
  organization: 1,
  kind: '',
  host_filter: null,
  variables: '---\nfoo: bar',
  has_active_failures: false,
  total_hosts: 0,
  hosts_with_active_failures: 0,
  total_groups: 0,
  groups_with_active_failures: 0,
  has_inventory_sources: false,
  total_inventory_sources: 0,
  inventory_sources_with_failures: 0,
  pending_deletion: false,
};

const associatedInstanceGroups = [
  {
    id: 1,
    name: 'Foo',
  },
];

function expectDetailToMatch(wrapper, label, value) {
  const detail = wrapper.find(`Detail[label="${label}"]`);
  expect(detail).toHaveLength(1);
  expect(detail.prop('value')).toEqual(value);
}

describe('<InventoryDetail />', () => {
  beforeEach(async () => {
    CredentialTypesAPI.read.mockResolvedValue({
      data: {
        results: [
          {
            id: 14,
            name: 'insights',
          },
        ],
      },
    });
  });
  test('should render details', async () => {
    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: {
        results: associatedInstanceGroups,
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryDetail inventory={mockInventory} />
      );
    });
    wrapper.update();
    expectDetailToMatch(wrapper, 'Name', mockInventory.name);
    expectDetailToMatch(wrapper, 'Description', mockInventory.description);
    expectDetailToMatch(wrapper, 'Type', 'Inventory');
    expectDetailToMatch(wrapper, 'Total hosts', mockInventory.total_hosts);
    const link = wrapper.find('Detail[label="Organization"]').find('Link');

    const org = wrapper.find('Detail[label="Organization"]');

    expect(link.prop('to')).toEqual('/organizations/1/details');
    expect(org.length).toBe(1);

    const vars = wrapper.find('VariablesDetail');
    expect(vars).toHaveLength(1);
    expect(vars.prop('value')).toEqual(mockInventory.variables);
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(mockInventory.created);
    expect(dates.at(1).prop('date')).toEqual(mockInventory.modified);
  });

  test('should have proper number of delete detail requests', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryDetail inventory={mockInventory} />
      );
    });
    expect(
      wrapper.find('DeleteButton').prop('deleteDetailsRequests')
    ).toHaveLength(2);
  });

  test('should load instance groups', async () => {
    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: {
        results: associatedInstanceGroups,
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryDetail inventory={mockInventory} />
      );
    });
    wrapper.update();
    expect(InventoriesAPI.readInstanceGroups).toHaveBeenCalledWith(
      mockInventory.id
    );
    const chip = wrapper.find('Chip').at(0);
    expect(chip.prop('isReadOnly')).toEqual(true);
    expect(chip.prop('children')).toEqual('Foo');
  });

  test('should not load instance groups', async () => {
    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: {
        results: [],
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryDetail inventory={mockInventory} />
      );
    });
    wrapper.update();
    expect(InventoriesAPI.readInstanceGroups).toHaveBeenCalledWith(
      mockInventory.id
    );
    expect(wrapper.find(`Detail[label="Instance Groups"]`)).toHaveLength(0);
  });
});
