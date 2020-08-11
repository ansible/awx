import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import CredentialTypeForm from './CredentialTypeForm';

jest.mock('../../../api');

const credentialType = {
  id: 28,
  type: 'credential_type',
  url: '/api/v2/credential_types/28/',
  summary_fields: {
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
  created: '2020-06-18T14:48:47.869002Z',
  modified: '2020 - 06 - 18T14: 48: 47.869017Z',
  name: 'Jenkins Credential',
  description: 'Jenkins Credential',
  kind: 'cloud',
  namespace: null,
  managed_by_tower: false,
  inputs: JSON.stringify({
    fields: [
      {
        id: 'username',
        type: 'string',
        label: 'Jenkins username',
      },
      {
        id: 'password',
        type: 'string',
        label: 'Jenkins password',
        secret: true,
      },
    ],
    required: ['username', 'password'],
  }),
  injectors: JSON.stringify({
    extra_vars: {
      Jenkins_password: '{{ password }}',
      Jenkins_username: '{{ username }}',
    },
  }),
};

describe('<CredentialTypeForm/>', () => {
  let wrapper;
  let onCancel;
  let onSubmit;

  beforeEach(async () => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialTypeForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          credentialType={credentialType}
        />
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should display form fields properly', () => {
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(
      wrapper.find('VariablesField[label="Input configuration"]').length
    ).toBe(1);
    expect(
      wrapper.find('VariablesField[label="Injector configuration"]').length
    ).toBe(1);
  });

  test('should call onSubmit when form submitted', async () => {
    expect(onSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  test('should update form values', () => {
    act(() => {
      wrapper.find('input#credential-type-name').simulate('change', {
        target: { value: 'Foo', name: 'name' },
      });
      wrapper.find('input#credential-type-description').simulate('change', {
        target: { value: 'New description', name: 'description' },
      });
    });
    wrapper.update();
    expect(wrapper.find('input#credential-type-name').prop('value')).toEqual(
      'Foo'
    );
    expect(
      wrapper.find('input#credential-type-description').prop('value')
    ).toEqual('New description');
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(onCancel).toBeCalled();
  });
});
