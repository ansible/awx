import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { ExecutionEnvironmentsAPI } from '../../../api';

import ExecutionEnvironmentForm from './ExecutionEnvironmentForm';

jest.mock('../../../api');

const mockMe = {
  is_superuser: true,
  is_super_auditor: false,
};

const executionEnvironment = {
  id: 16,
  name: 'Test EE',
  type: 'execution_environment',
  container_options: 'one',
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

const mockOptions = {
  data: {
    actions: {
      POST: {
        container_options: {
          choices: [
            ['one', 'One'],
            ['two', 'Two'],
            ['three', 'Three'],
          ],
        },
      },
    },
  },
};

describe('<ExecutionEnvironmentForm/>', () => {
  let wrapper;
  let onCancel;
  let onSubmit;

  beforeEach(async () => {
    onCancel = jest.fn();
    onSubmit = jest.fn();
    ExecutionEnvironmentsAPI.readOptions.mockResolvedValue(mockOptions);
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          executionEnvironment={executionEnvironment}
          options={mockOptions}
          me={mockMe}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should display form fields properly', () => {
    expect(wrapper.find('FormGroup[label="Image name"]').length).toBe(1);
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

  test('should update form values', async () => {
    await act(async () => {
      wrapper.find('input#execution-environment-image').simulate('change', {
        target: {
          value: 'Updated EE Name',
          name: 'name',
        },
      });
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

      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 3,
        name: 'organization',
      });
    });

    wrapper.update();
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 3,
      name: 'organization',
    });
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
