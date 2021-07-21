import React from 'react';
import { act } from 'react-dom/test-utils';
import { ExecutionEnvironmentsAPI, CredentialTypesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

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
  pull: 'one',
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
    organization: {
      id: 1,
      name: 'Default',
      description: '',
    },
    credential: {
      id: 4,
      name: 'Container Registry',
      description: '',
      kind: 'registry',
      cloud: false,
      kubernetes: false,
      credential_type_id: 17,
    },
  },
  created: '2020-09-17T16:06:57.346128Z',
  modified: '2020-09-17T16:06:57.346147Z',
  description: 'A simple EE',
  organization: 1,
  image: 'https://registry.com/image/container',
  managed: false,
  credential: 4,
};

const globallyAvailableEE = {
  id: 17,
  name: 'GEE',
  type: 'execution_environment',
  pull: 'one',
  url: '/api/v2/execution_environments/17/',
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
      description: '',
      kind: 'registry',
      cloud: false,
      kubernetes: false,
      credential_type_id: 17,
    },
  },
  created: '2020-09-17T16:06:57.346128Z',
  modified: '2020-09-17T16:06:57.346147Z',
  description: 'A simple EE',
  organization: null,
  image: 'https://registry.com/image/container',
  managed: false,
  credential: 4,
};

const mockOptions = {
  data: {
    actions: {
      POST: {
        pull: {
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

const containerRegistryCredentialResolve = {
  data: {
    results: [
      {
        id: 4,
        name: 'Container Registry',
        kind: 'registry',
      },
    ],
    count: 1,
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
    CredentialTypesAPI.read.mockResolvedValue(
      containerRegistryCredentialResolve
    );
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
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
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

  test('globally available EE can not have organization reassigned', async () => {
    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <ExecutionEnvironmentForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          executionEnvironment={globallyAvailableEE}
          options={mockOptions}
          me={mockMe}
          isOrgLookupDisabled
        />
      );
    });
    await waitForElement(newWrapper, 'ContentLoading', (el) => el.length === 0);
    expect(newWrapper.find('OrganizationLookup').prop('isDisabled')).toEqual(
      true
    );
    expect(newWrapper.find('Tooltip').prop('content')).toEqual(
      'Globally available execution environment can not be reassigned to a specific Organization'
    );
  });

  test('should allow an organization to be re-assigned as globally available EE', async () => {
    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <ExecutionEnvironmentForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          executionEnvironment={executionEnvironment}
          options={mockOptions}
          me={mockMe}
          isOrgLookupDisabled
        />
      );
    });
    await waitForElement(newWrapper, 'ContentLoading', (el) => el.length === 0);
    expect(newWrapper.find('OrganizationLookup').prop('isDisabled')).toEqual(
      false
    );
    expect(newWrapper.find('Tooltip').length).toEqual(0);

    await act(async () => {
      newWrapper.find('OrganizationLookup').invoke('onBlur')();
      newWrapper.find('OrganizationLookup').invoke('onChange')(null);
    });
    newWrapper.update();
    expect(newWrapper.find('OrganizationLookup').prop('value')).toEqual(null);
  });

  test('should disable edition for managed EEs, except pull option', async () => {
    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <ExecutionEnvironmentForm
          onCancel={onCancel}
          onSubmit={onSubmit}
          executionEnvironment={{ ...executionEnvironment, managed: true }}
          options={mockOptions}
          me={mockMe}
        />
      );
    });
    await waitForElement(newWrapper, 'ContentLoading', (el) => el.length === 0);
    expect(newWrapper.find('OrganizationLookup').prop('isDisabled')).toEqual(
      true
    );
    expect(newWrapper.find('CredentialLookup').prop('isDisabled')).toEqual(
      true
    );
    expect(
      newWrapper
        .find('TextInputBase[id="execution-environment-name"]')
        .prop('isDisabled')
    ).toEqual(true);
    expect(
      newWrapper
        .find('TextInputBase[id="execution-environment-description"]')
        .prop('isDisabled')
    ).toEqual(true);
    expect(
      newWrapper
        .find('TextInputBase[id="execution-environment-image"]')
        .prop('isDisabled')
    ).toEqual(true);
    expect(
      newWrapper
        .find('FormSelect[id="container-pull-options"]')
        .prop('isDisabled')
    ).toEqual(false);
  });
});
