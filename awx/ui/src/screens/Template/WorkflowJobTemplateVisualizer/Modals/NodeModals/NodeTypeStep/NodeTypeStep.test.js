import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import {
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
import { useUserProfile } from 'contexts/Config';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';

import NodeTypeStep from './NodeTypeStep';

jest.mock('../../../../../../api/models/InventorySources');
jest.mock('../../../../../../api/models/JobTemplates');
jest.mock('../../../../../../api/models/Projects');
jest.mock('../../../../../../api/models/WorkflowJobTemplates');

describe('NodeTypeStep', () => {
  beforeEach(() => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: true,
        isSystemAuditor: false,
        isOrgAdmin: false,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
  });
  beforeAll(() => {
    JobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Job Template',
            type: 'job_template',
            url: '/api/v2/job_templates/1',
          },
        ],
      },
    });
    JobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    ProjectsAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Project',
            type: 'project',
            url: '/api/v2/projects/1',
          },
        ],
      },
    });
    ProjectsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    InventorySourcesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Inventory Source',
            type: 'inventory_source',
            url: '/api/v2/inventory_sources/1',
          },
        ],
      },
    });
    InventorySourcesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    WorkflowJobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Workflow Job Template',
            type: 'workflow_job_template',
            url: '/api/v2/workflow_job_templates/1',
          },
        ],
      },
    });
    WorkflowJobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });
  afterAll(() => {
    jest.clearAllMocks();
  });
  test('It shows the job template list by default', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ nodeType: 'job_template' }}>
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe('job_template');
    expect(wrapper.find('JobTemplatesList').length).toBe(1);
  });
  test('It shows the project list when node type is project', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ nodeType: 'project' }}>
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe('project');
    expect(wrapper.find('ProjectsList').length).toBe(1);
  });
  test('It shows the inventory source list when node type is inventory source', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ nodeType: 'inventory_source' }}>
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe(
      'inventory_source'
    );
    expect(wrapper.find('InventorySourcesList').length).toBe(1);
  });
  test('It shows the workflow job template list when node type is workflow job template', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ nodeType: 'workflow_job_template' }}>
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe(
      'workflow_job_template'
    );
    expect(wrapper.find('WorkflowJobTemplatesList').length).toBe(1);
  });
  test('It shows the approval form fields when node type is approval', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            nodeType: 'workflow_approval_template',
            approvalName: '',
            approvalDescription: '',
            timeoutMinutes: 0,
            timeoutSeconds: 0,
            convergence: 'any',
          }}
        >
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe(
      'workflow_approval_template'
    );
    expect(wrapper.find('FormField[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormField[label="Description"]').length).toBe(1);
    expect(wrapper.find('input[name="timeoutMinutes"]').length).toBe(1);
    expect(wrapper.find('input[name="timeoutSeconds"]').length).toBe(1);

    await act(async () => {
      wrapper.find('input#approval-name').simulate('change', {
        target: { value: 'Test Approval', name: 'approvalName' },
      });
      wrapper.find('input#approval-description').simulate('change', {
        target: {
          value: 'Test Approval Description',
          name: 'approvalDescription',
        },
      });
      wrapper.find('input[name="timeoutMinutes"]').simulate('change', {
        target: { value: 5, name: 'timeoutMinutes' },
      });
      wrapper.find('input[name="timeoutSeconds"]').simulate('change', {
        target: { value: 30, name: 'timeoutSeconds' },
      });
    });

    wrapper.update();

    expect(wrapper.find('input#approval-name').prop('value')).toBe(
      'Test Approval'
    );
    expect(wrapper.find('input#approval-description').prop('value')).toBe(
      'Test Approval Description'
    );
    expect(wrapper.find('input[name="timeoutMinutes"]').prop('value')).toBe(5);
    expect(wrapper.find('input[name="timeoutSeconds"]').prop('value')).toBe(30);
  });

  test('it does not show management job as a choice for non system admin', async () => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: false,
        isSystemAuditor: false,
        isOrgAdmin: true,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ nodeType: 'workflow_job_template' }}>
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('data').length).toBe(5);
    expect(
      wrapper
        .find('AnsibleSelect')
        .prop('data')
        .map((item) => item.key)
    ).toEqual([
      'workflow_approval_template',
      'inventory_source',
      'job_template',
      'project',
      'workflow_job_template',
    ]);
  });

  test('it does show management job as a choice for system admin', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ nodeType: 'workflow_job_template' }}>
          <NodeTypeStep />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('data').length).toBe(6);
    expect(
      wrapper
        .find('AnsibleSelect')
        .prop('data')
        .map((item) => item.key)
    ).toEqual([
      'workflow_approval_template',
      'inventory_source',
      'job_template',
      'project',
      'workflow_job_template',
      'system_job_template',
    ]);
  });
});
