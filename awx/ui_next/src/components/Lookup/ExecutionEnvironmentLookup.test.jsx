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
    ProjectsAPI.readDetail.mockResolvedValue({ data: { organization: 39 } });
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

  test('should call api with organization id', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentLookup
          value={executionEnvironment}
          onChange={() => {}}
          organizationId={1}
          globallyAvailable
        />
      );
    });
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalledWith({
      or__organization__id: 1,
      or__organization__isnull: 'True',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });

  test('should call api with organization id from the related project', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentLookup
          value={executionEnvironment}
          onChange={() => {}}
          projectId={12}
          globallyAvailable
        />
      );
    });
    expect(ProjectsAPI.readDetail).toHaveBeenCalledWith(12);
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalledWith({
      or__organization__id: 39,
      or__organization__isnull: 'True',
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
});
