import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InventoriesAPI, CredentialTypesAPI } from '../../../api';
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
    insights_credential: {
      id: 1,
      name: 'Foo',
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
  insights_credential: null,
  pending_deletion: false,
};

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
const associatedInstanceGroups = [
  {
    id: 1,
    name: 'Foo',
  },
];
InventoriesAPI.readInstanceGroups.mockResolvedValue({
  data: {
    results: associatedInstanceGroups,
  },
});

function expectDetailToMatch(wrapper, label, value) {
  const detail = wrapper.find(`Detail[label="${label}"]`);
  expect(detail).toHaveLength(1);
  expect(detail.prop('value')).toEqual(value);
}

describe('<InventoryDetail />', () => {
  test('should render details', async () => {
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
    const org = wrapper.find('Detail[label="Organization"]');
    expect(org.prop('value')).toMatchInlineSnapshot(`
      <ForwardRef
        to="/organizations/1/details"
      >
        The Organization
      </ForwardRef>
    `);
    const vars = wrapper.find('VariablesDetail');
    expect(vars).toHaveLength(1);
    expect(vars.prop('value')).toEqual(mockInventory.variables);
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(mockInventory.created);
    expect(dates.at(1).prop('date')).toEqual(mockInventory.modified);
  });

  test('should load instance groups', async () => {
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
});
