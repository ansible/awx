import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import InventoryForm from './InventoryForm';

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
  variables: '---',
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

const instanceGroups = [{ name: 'Foo', id: 1 }, { name: 'Bar', id: 2 }];
describe('<InventoryForm />', () => {
  let wrapper;
  let onCancel;
  let onSubmit;
  beforeEach(() => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
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
  afterEach(() => {
    wrapper.unmount();
  });
  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('should display form fields properly', () => {
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Organization"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Instance Groups"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Insights Credential"]').length).toBe(
      1
    );
    expect(wrapper.find('VariablesField[label="Variables"]').length).toBe(1);
  });
  test('should update from values onChange', async () => {
    const form = wrapper.find('Formik');
    act(() => {
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 3,
        name: 'organization',
      });
    });
    expect(form.state('values').organization).toEqual({
      id: 3,
      name: 'organization',
    });
    wrapper.find('input#inventory-name').simulate('change', {
      target: { value: 'new Foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new Foo');
    act(() => {
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 10,
        name: 'credential',
      });
    });
    expect(form.state('values').insights_credential).toEqual({
      id: 10,
      name: 'credential',
    });

    form.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(onSubmit).toHaveBeenCalledWith({
      description: '',
      insights_credential: { id: 10, name: 'credential' },
      instanceGroups: [{ id: 1, name: 'Foo' }, { id: 2, name: 'Bar' }],
      name: 'new Foo',
      organization: { id: 3, name: 'organization' },
      variables: '---',
    });
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(onCancel).toBeCalled();
  });
});
