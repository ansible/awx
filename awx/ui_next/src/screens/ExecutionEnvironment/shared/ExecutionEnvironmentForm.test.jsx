import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentForm from './ExecutionEnvironmentForm';

jest.mock('../../../api');

const executionEnvironment = {
  id: 16,
  type: 'execution_environment',
  url: '/api/v2/execution_environments/16/',
  related: {
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    activity_stream: '/api/v2/execution_environments/16/activity_stream/',
    unified_job_templates:
      '/api/v2/execution_environments/16/unified_job_templates/',
    credential: '/api/v2/credentials/4/',
  },
  summary_fields: {
    credential: {
      id: 4,
      name: 'Container Registry',
    },
  },
  created: '2020-09-17T16:06:57.346128Z',
  modified: '2020-09-17T16:06:57.346147Z',
  description: 'A simple EE',
  organization: null,
  image: 'https://registry.com/image/container',
  managed_by_tower: false,
  credential: 4,
};

describe('<ExecutionEnvironmentForm/>', () => {
  let wrapper;
  let onCancel;
  let onSubmit;

  beforeEach(async () => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          executionEnvironment={executionEnvironment}
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
    expect(wrapper.find('FormGroup[label="Image"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('CredentialLookup').length).toBe(1);
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
      wrapper.find('input#execution-environment-image').simulate('change', {
        target: {
          value: 'https://registry.com/image/container2',
          name: 'image',
        },
      });
      wrapper
        .find('input#execution-environment-description')
        .simulate('change', {
          target: { value: 'New description', name: 'description' },
        });
      wrapper.find('CredentialLookup').invoke('onBlur')();
      wrapper.find('CredentialLookup').invoke('onChange')({
        id: 99,
        name: 'credential',
      });
    });
    wrapper.update();
    expect(
      wrapper.find('input#execution-environment-image').prop('value')
    ).toEqual('https://registry.com/image/container2');
    expect(
      wrapper.find('input#execution-environment-description').prop('value')
    ).toEqual('New description');
    expect(wrapper.find('CredentialLookup').prop('value')).toEqual({
      id: 99,
      name: 'credential',
    });
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(onCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(onCancel).toBeCalled();
  });
});
