import React from 'react';
import { act } from 'react-dom/test-utils';
import { LabelsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InventoryForm from './InventoryForm';

jest.mock('../../../api');

const inventory = {
  id: 1,
  type: 'inventory',
  url: '/api/v2/inventories/1/',
  summary_fields: {
    organization: {
      id: 1,
      name: 'Default',
      description: '',
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      adhoc: true,
    },
    labels: {
      results: [
        { name: 'Sushi', id: 1 },
        { name: 'Major', id: 2 },
      ],
    },
  },
  created: '2019-10-04T16:56:48.025455Z',
  modified: '2019-10-04T16:56:48.025468Z',
  name: 'Inv no hosts',
  description: '',
  organization: 1,
  kind: '',
  host_filter: null,
  variables: '---',
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

const instanceGroups = [
  { name: 'Foo', id: 1 },
  { name: 'Bar', id: 2 },
];
describe('<InventoryForm />', () => {
  let wrapper;
  let onCancel;
  let onSubmit;

  beforeAll(async () => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
    LabelsAPI.read.mockReturnValue({
      data: inventory.summary_fields.labels,
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          inventory={inventory}
          instanceGroups={instanceGroups}
          credentialTypeId={14}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should display form fields properly', async () => {
    await waitForElement(wrapper, 'InventoryForm', (el) => el.length > 0);

    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Instance Groups"]').length).toBe(1);
    expect(wrapper.find('VariablesField[label="Variables"]').length).toBe(1);
    expect(wrapper.find('CodeEditor').prop('value')).toEqual('---');
  });

  test('should update form values', async () => {
    await act(async () => {
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 3,
        name: 'organization',
      });

      wrapper.find('input#inventory-name').simulate('change', {
        target: { value: 'new Foo', name: 'name' },
      });
    });
    wrapper.update();
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 3,
      name: 'organization',
    });
    expect(wrapper.find('input#inventory-name').prop('value')).toEqual(
      'new Foo'
    );
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(onCancel).toBeCalled();
  });

  test('should render LabelsSelect', async () => {
    const select = wrapper.find('LabelSelect');
    expect(select).toHaveLength(1);
    expect(select.prop('value')).toEqual(
      inventory.summary_fields.labels.results
    );
  });
});
