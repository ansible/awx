import React from 'react';
import { act } from 'react-dom/test-utils';

import { ExecutionEnvironmentsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentTemplateList from './ExecutionEnvironmentTemplateList';

jest.mock('../../../api/');

const templates = {
  data: {
    count: 3,
    results: [
      {
        id: 1,
        type: 'job_template',
        name: 'Foo',
        url: '/api/v2/job_templates/1/',
        related: {
          execution_environment: '/api/v2/execution_environments/1/',
        },
      },
      {
        id: 2,
        type: 'workflow_job_template',
        name: 'Bar',
        url: '/api/v2/workflow_job_templates/2/',
        related: {
          execution_environment: '/api/v2/execution_environments/1/',
        },
      },
      {
        id: 3,
        type: 'job_template',
        name: 'Fuzz',
        url: '/api/v2/job_templates/3/',
        related: {
          execution_environment: '/api/v2/execution_environments/1/',
        },
      },
    ],
  },
};

const mockExecutionEnvironment = {
  id: 1,
  name: 'Default EE',
};

const options = { data: { actions: { GET: {} } } };

describe('<ExecutionEnvironmentTemplateList/>', () => {
  let wrapper;

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentTemplateList
          executionEnvironment={mockExecutionEnvironment}
        />
      );
    });
    await waitForElement(
      wrapper,
      'ExecutionEnvironmentTemplateList',
      (el) => el.length > 0
    );
  });

  test('should have data fetched and render 3 rows', async () => {
    ExecutionEnvironmentsAPI.readUnifiedJobTemplates.mockResolvedValue(
      templates
    );

    ExecutionEnvironmentsAPI.readUnifiedJobTemplateOptions.mockResolvedValue(
      options
    );

    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentTemplateList
          executionEnvironment={mockExecutionEnvironment}
        />
      );
    });
    await waitForElement(
      wrapper,
      'ExecutionEnvironmentTemplateList',
      (el) => el.length > 0
    );

    expect(wrapper.find('ExecutionEnvironmentTemplateListItem').length).toBe(3);
    expect(ExecutionEnvironmentsAPI.readUnifiedJobTemplates).toBeCalled();
    expect(ExecutionEnvironmentsAPI.readUnifiedJobTemplateOptions).toBeCalled();
  });

  test('should not render add button', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentTemplateList
          executionEnvironment={mockExecutionEnvironment}
        />
      );
    });
    waitForElement(
      wrapper,
      'ExecutionEnvironmentTemplateList',
      (el) => el.length > 0
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
