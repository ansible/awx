import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ContainerGroupForm from './ContainerGroupForm';

jest.mock('../../../api');

const instanceGroup = {
  id: 7,
  type: 'instance_group',
  url: '/api/v2/instance_groups/7/',
  related: {
    jobs: '/api/v2/instance_groups/7/jobs/',
    instances: '/api/v2/instance_groups/7/instances/',
  },
  name: 'Bar',
  created: '2020-07-21T18:41:02.818081Z',
  modified: '2020-07-24T20:32:03.121079Z',
  capacity: 24,
  committed_capacity: 0,
  consumed_capacity: 0,
  percent_capacity_remaining: 100.0,
  jobs_running: 0,
  jobs_total: 0,
  instances: 1,
  controller: null,
  is_controller: false,
  is_isolated: false,
  is_containerized: false,
  credential: 3,
  policy_instance_percentage: 46,
  policy_instance_minimum: 12,
  policy_instance_list: [],
  pod_spec_override: '',
  summary_fields: {
    credential: {
      id: 3,
      name: 'test',
      description: 'Simple one',
      kind: 'kubernetes_bearer_token',
      cloud: false,
      kubernetes: true,
      credential_type_id: 17,
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
};

const initialPodSpec = {
  default: {
    apiVersion: 'v1',
    kind: 'Pod',
    metadata: {
      namespace: 'default',
    },
    spec: {
      containers: [
        {
          image: 'ansible/ansible-runner',
          tty: true,
          stdin: true,
          imagePullPolicy: 'Always',
          args: ['sleep', 'infinity'],
        },
      ],
    },
  },
};

describe('<ContainerGroupForm/>', () => {
  let wrapper;
  let onCancel;
  let onSubmit;

  beforeEach(async () => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <ContainerGroupForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          instanceGroup={instanceGroup}
          initialPodSpec={initialPodSpec}
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
    expect(wrapper.find('VariablesField[label="Custom pod spec"]').length).toBe(
      0
    );
    expect(
      wrapper
        .find('Checkbox[aria-label="Customize pod specification"]')
        .prop('isChecked')
    ).toBeFalsy();
    expect(wrapper.find('CredentialLookup').prop('value').name).toBe('test');
  });

  test('should update form values', () => {
    act(() => {
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 99,
        name: 'credential',
      });
      wrapper.find('TextInputBase#container-group-name').simulate('change', {
        target: { value: 'new Foo', name: 'name' },
      });
    });
    wrapper.update();
    expect(wrapper.find('CredentialLookup').prop('value')).toEqual({
      id: 99,
      name: 'credential',
    });
    expect(
      wrapper.find('TextInputBase#container-group-name').prop('value')
    ).toEqual('new Foo');
  });

  test('should call onSubmit when form submitted', async () => {
    expect(onSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(onCancel).toBeCalled();
  });
});
