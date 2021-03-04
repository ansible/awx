import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ExecutionEnvironmentLookup from './ExecutionEnvironmentLookup';
import { ExecutionEnvironmentsAPI, ProjectsAPI } from '../../api';

jest.mock('../../api');

const mockedExecutionEnvironments = {
  count: 1,
  results: [
    {
      id: 2,
      name: 'Foo',
      image: 'quay.io/ansible/awx-ee',
      pull: 'missing',
    },
  ],
};

const executionEnvironment = {
  id: 42,
  name: 'Bar',
  image: 'quay.io/ansible/bar',
  pull: 'missing',
};

describe('ExecutionEnvironmentLookup', () => {
  let wrapper;

  beforeEach(() => {
    ExecutionEnvironmentsAPI.read.mockResolvedValue(
      mockedExecutionEnvironments
    );
    ProjectsAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Fuz',
          },
        ],
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should render successfully', async () => {
    ExecutionEnvironmentsAPI.readOptions.mockReturnValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentLookup
          isDefaultEnvironment
          value={executionEnvironment}
          onChange={() => {}}
        />
      );
    });
    wrapper.update();
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalledTimes(2);
    expect(wrapper.find('ExecutionEnvironmentLookup')).toHaveLength(1);
    expect(
      wrapper.find('FormGroup[label="Default Execution Environment"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Execution Environment"]').length
    ).toBe(0);
  });

  test('should fetch execution environments', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentLookup
          value={executionEnvironment}
          onChange={() => {}}
        />
      );
    });
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalledTimes(2);
    expect(
      wrapper.find('FormGroup[label="Default Execution Environment"]').length
    ).toBe(0);
    expect(
      wrapper.find('FormGroup[label="Execution Environment"]').length
    ).toBe(1);
  });
});
