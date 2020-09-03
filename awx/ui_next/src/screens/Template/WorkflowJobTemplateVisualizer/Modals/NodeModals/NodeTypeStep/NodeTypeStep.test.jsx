import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../../testUtils/enzymeHelpers';
import {
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplatesAPI,
} from '../../../../../../api';
import NodeTypeStep from './NodeTypeStep';

jest.mock('../../../../../../api/models/InventorySources');
jest.mock('../../../../../../api/models/JobTemplates');
jest.mock('../../../../../../api/models/Projects');
jest.mock('../../../../../../api/models/WorkflowJobTemplates');

const onUpdateDescription = jest.fn();
const onUpdateName = jest.fn();
const onUpdateNodeResource = jest.fn();
const onUpdateNodeType = jest.fn();
const onUpdateTimeout = jest.fn();

describe('NodeTypeStep', () => {
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
        <NodeTypeStep
          onUpdateDescription={onUpdateDescription}
          onUpdateName={onUpdateName}
          onUpdateNodeResource={onUpdateNodeResource}
          onUpdateNodeType={onUpdateNodeType}
          onUpdateTimeout={onUpdateTimeout}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe('job_template');
    expect(wrapper.find('JobTemplatesList').length).toBe(1);
    wrapper.find('Radio').simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 1,
      name: 'Test Job Template',
      type: 'job_template',
      url: '/api/v2/job_templates/1',
    });
  });
  test('It shows the project list when node type is project sync', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <NodeTypeStep
          nodeType="project_sync"
          onUpdateDescription={onUpdateDescription}
          onUpdateName={onUpdateName}
          onUpdateNodeResource={onUpdateNodeResource}
          onUpdateNodeType={onUpdateNodeType}
          onUpdateTimeout={onUpdateTimeout}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe('project_sync');
    expect(wrapper.find('ProjectsList').length).toBe(1);
    wrapper.find('Radio').simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 1,
      name: 'Test Project',
      type: 'project',
      url: '/api/v2/projects/1',
    });
  });
  test('It shows the inventory source list when node type is inventory source sync', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <NodeTypeStep
          nodeType="inventory_source_sync"
          onUpdateDescription={onUpdateDescription}
          onUpdateName={onUpdateName}
          onUpdateNodeResource={onUpdateNodeResource}
          onUpdateNodeType={onUpdateNodeType}
          onUpdateTimeout={onUpdateTimeout}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe(
      'inventory_source_sync'
    );
    expect(wrapper.find('InventorySourcesList').length).toBe(1);
    wrapper.find('Radio').simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 1,
      name: 'Test Inventory Source',
      type: 'inventory_source',
      url: '/api/v2/inventory_sources/1',
    });
  });
  test('It shows the workflow job template list when node type is workflow job template', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <NodeTypeStep
          nodeType="workflow_job_template"
          onUpdateDescription={onUpdateDescription}
          onUpdateName={onUpdateName}
          onUpdateNodeResource={onUpdateNodeResource}
          onUpdateNodeType={onUpdateNodeType}
          onUpdateTimeout={onUpdateTimeout}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe(
      'workflow_job_template'
    );
    expect(wrapper.find('WorkflowJobTemplatesList').length).toBe(1);
    wrapper.find('Radio').simulate('click');
    expect(onUpdateNodeResource).toHaveBeenCalledWith({
      id: 1,
      name: 'Test Workflow Job Template',
      type: 'workflow_job_template',
      url: '/api/v2/workflow_job_templates/1',
    });
  });
  test('It shows the approval form fields when node type is approval', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <NodeTypeStep
          nodeType="approval"
          onUpdateDescription={onUpdateDescription}
          onUpdateName={onUpdateName}
          onUpdateNodeResource={onUpdateNodeResource}
          onUpdateNodeType={onUpdateNodeType}
          onUpdateTimeout={onUpdateTimeout}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe('approval');
    expect(wrapper.find('input#approval-name').length).toBe(1);
    expect(wrapper.find('input#approval-description').length).toBe(1);
    expect(wrapper.find('input#approval-timeout-minutes').length).toBe(1);
    expect(wrapper.find('input#approval-timeout-seconds').length).toBe(1);

    await act(async () => {
      wrapper.find('input#approval-name').simulate('change', {
        target: { value: 'Test Approval', name: 'name' },
      });
    });

    expect(onUpdateName).toHaveBeenCalledWith('Test Approval');

    await act(async () => {
      wrapper.find('input#approval-description').simulate('change', {
        target: { value: 'Test Approval Description', name: 'description' },
      });
    });

    expect(onUpdateDescription).toHaveBeenCalledWith(
      'Test Approval Description'
    );

    await act(async () => {
      wrapper.find('input#approval-timeout-minutes').simulate('change', {
        target: { value: 5, name: 'timeoutMinutes' },
      });
    });

    expect(onUpdateTimeout).toHaveBeenCalledWith(300);

    await act(async () => {
      wrapper.find('input#approval-timeout-seconds').simulate('change', {
        target: { value: 30, name: 'timeoutSeconds' },
      });
    });

    expect(onUpdateTimeout).toHaveBeenCalledWith(330);
  });
});
