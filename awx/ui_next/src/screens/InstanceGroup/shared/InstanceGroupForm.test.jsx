import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import InstanceGroupForm from './InstanceGroupForm';

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
  credential: null,
  policy_instance_percentage: 46,
  policy_instance_minimum: 12,
  policy_instance_list: [],
  pod_spec_override: '',
  summary_fields: {
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
};

describe('<InstanceGroupForm/>', () => {
  let wrapper;
  let onCancel;
  let onSubmit;

  beforeEach(async () => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          instanceGroup={instanceGroup}
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
    expect(
      wrapper.find('FormGroup[label="Policy instance minimum"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Policy instance percentage"]').length
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
      wrapper.find('input#instance-group-name').simulate('change', {
        target: { value: 'Foo', name: 'name' },
      });
      wrapper
        .find('input#instance-group-policy-instance-minimum')
        .simulate('change', {
          target: { value: 10, name: 'policy_instance_minimum' },
        });
    });
    wrapper.update();
    expect(wrapper.find('input#instance-group-name').prop('value')).toEqual(
      'Foo'
    );
    expect(
      wrapper.find('input#instance-group-policy-instance-minimum').prop('value')
    ).toEqual(10);
    expect(
      wrapper
        .find('input#instance-group-policy-instance-percentage')
        .prop('value')
    ).toEqual(46);
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(onCancel).toBeCalled();
  });
});
