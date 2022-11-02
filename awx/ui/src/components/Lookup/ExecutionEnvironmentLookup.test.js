import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { ExecutionEnvironmentsAPI, ProjectsAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ExecutionEnvironmentLookup from './ExecutionEnvironmentLookup';

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
    ExecutionEnvironmentsAPI.read.mockResolvedValue({
      data: mockedExecutionEnvironments,
    });
    ProjectsAPI.readDetail.mockResolvedValue({ data: { organization: 39 } });
  });

  afterEach(() => {
    jest.clearAllMocks();
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
        <Formik>
          <ExecutionEnvironmentLookup
            value={executionEnvironment}
            onChange={() => {}}
          />
        </Formik>
      );
    });
    wrapper.update();
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalledTimes(1);
    expect(wrapper.find('ExecutionEnvironmentLookup')).toHaveLength(1);
    expect(
      wrapper.find('FormGroup[label="Execution Environment"]').length
    ).toBe(1);
    expect(wrapper.find('Checkbox[aria-label="Prompt on launch"]').length).toBe(
      0
    );
  });

  test('should fetch execution environments', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <ExecutionEnvironmentLookup
            value={executionEnvironment}
            onChange={() => {}}
          />
        </Formik>
      );
    });
    expect(ExecutionEnvironmentsAPI.read).toHaveBeenCalledTimes(1);
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
        <Formik>
          <ExecutionEnvironmentLookup
            value={executionEnvironment}
            onChange={() => {}}
            organizationId={1}
            globallyAvailable
          />
        </Formik>
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
        <Formik>
          <ExecutionEnvironmentLookup
            value={executionEnvironment}
            onChange={() => {}}
            projectId={12}
            globallyAvailable
          />
        </Formik>
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

  test('should render prompt on launch checkbox when necessary', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <ExecutionEnvironmentLookup
            value={executionEnvironment}
            onChange={() => {}}
            projectId={12}
            globallyAvailable
            isPromptableField
            promptId="ee-prompt"
            promptName="ask_execution_environment_on_launch"
          />
        </Formik>
      );
    });
    expect(wrapper.find('Checkbox[aria-label="Prompt on launch"]').length).toBe(
      1
    );
  });
});
