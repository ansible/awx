import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { useUserProfile } from 'contexts/Config';
import {
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
import {
  waitForElement,
  mountWithContexts,
} from '../../../../../../testUtils/enzymeHelpers';
import NodeModal from './NodeModal';

let wrapper;
jest.mock('../../../../../api');
const dispatch = jest.fn();
const onSave = jest.fn();

const jtLaunchConfig = {
  can_start_without_user_input: false,
  passwords_needed_to_start: [],
  ask_scm_branch_on_launch: false,
  ask_variables_on_launch: true,
  ask_tags_on_launch: true,
  ask_diff_mode_on_launch: true,
  ask_skip_tags_on_launch: true,
  ask_job_type_on_launch: true,
  ask_limit_on_launch: false,
  ask_verbosity_on_launch: true,
  ask_inventory_on_launch: true,
  ask_credential_on_launch: true,
  survey_enabled: true,
  variables_needed_to_start: ['a'],
  credential_needed_to_start: false,
  inventory_needed_to_start: false,
  job_template_data: {
    name: 'A User-2 has admin permission',
    id: 25,
    description: '',
  },
  defaults: {
    extra_vars: '---',
    diff_mode: false,
    limit: '',
    job_tags: '',
    skip_tags: '',
    job_type: 'run',
    verbosity: 0,
    inventory: {
      name: ' Inventory 1 Org 0',
      id: 1,
    },
    credentials: [
      {
        id: 2,
        name: ' Credential 2 User 1',
        credential_type: 1,
        passwords_needed: [],
      },
      {
        id: 8,
        name: 'vault cred',
        credential_type: 3,
        passwords_needed: [],
        vault_id: '',
      },
    ],
    scm_branch: '',
  },
};

const mockJobTemplate = {
  id: 1,
  name: 'Test Job Template',
  type: 'job_template',
  url: '/api/v2/job_templates/1',
  summary_fields: {
    inventory: {
      name: 'Foo Inv',
      id: 1,
    },
    recent_jobs: [],
  },
  related: { webhook_receiver: '' },
  inventory: 1,
  project: 5,
};

describe('NodeModal', () => {
  beforeEach(async () => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: true,
        isSystemAuditor: false,
        isOrgAdmin: false,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
    JobTemplatesAPI.read = jest.fn();
    JobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [mockJobTemplate],
      },
    });
    JobTemplatesAPI.readOptions = jest.fn();
    JobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    JobTemplatesAPI.readLaunch = jest.fn();
    JobTemplatesAPI.readLaunch.mockResolvedValue({ data: jtLaunchConfig });
    JobTemplatesAPI.readCredentials = jest.fn();
    JobTemplatesAPI.readCredentials.mockResolvedValue({
      data: {
        results: [],
      },
    });
    JobTemplatesAPI.readSurvey = jest.fn();
    JobTemplatesAPI.readSurvey.mockResolvedValue({
      data: {
        name: '',
        description: '',
        spec: [
          {
            question_name: 'Foo',
            required: true,
            variable: 'bar',
            type: 'text',
            default: 'answer',
          },
        ],
        type: 'text',
        variable: 'bar',
      },
    });
    ProjectsAPI.read = jest.fn();
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
    ProjectsAPI.readOptions = jest.fn();
    ProjectsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    InventorySourcesAPI.read = jest.fn();
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
    InventorySourcesAPI.readOptions = jest.fn();
    InventorySourcesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    WorkflowJobTemplatesAPI.read = async () => ({
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
    WorkflowJobTemplatesAPI.readOptions = async () => ({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    WorkflowJobTemplatesAPI.readLaunch = async () => ({
      data: {
        ask_inventory_on_launch: false,
        ask_limit_on_launch: false,
        ask_scm_branch_on_launch: false,
        can_start_without_user_input: false,
        defaults: {
          extra_vars: '---',
          inventory: {
            name: null,
            id: null,
          },
          limit: '',
          scm_branch: '',
        },
        survey_enabled: false,
        variables_needed_to_start: [],
        node_templates_missing: [],
        node_prompts_rejected: [272, 273],
        workflow_job_template_data: {
          name: 'jt',
          id: 53,
          description: '',
        },
        ask_variables_on_launch: false,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              nodeToEdit: null,
            }}
          >
            <NodeModal
              askLinkType
              onSave={onSave}
              title="Add Node"
              resourceDefaultCredentials={[]}
            />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });
    await waitForElement(wrapper, 'PFWizard');
  });

  test('Can successfully create a new job template node', async () => {
    act(() => {
      wrapper.find('SelectableCard#link-type-always').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('td#check-action-item-1').find('input').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });

    wrapper.update();

    expect(JobTemplatesAPI.readLaunch).toBeCalledWith(1);
    expect(JobTemplatesAPI.readCredentials).toBeCalledWith(1, {
      page_size: 200,
    });
    expect(JobTemplatesAPI.readSurvey).toBeCalledWith(25);
    wrapper.update();
    expect(wrapper.find('NodeNextButton').prop('buttonText')).toBe('Next');
    act(() => {
      wrapper.find('StepName#preview-step').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('NodeNextButton').prop('buttonText')).toBe('Save');
    act(() => {
      wrapper.find('NodeNextButton').prop('onClick')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        linkType: 'always',
        nodeType: 'job_template',
        inventory: { name: 'Foo Inv', id: 1 },
        credentials: [],
        job_type: '',
        verbosity: '0',
        job_tags: '',
        skip_tags: '',
        diff_mode: false,
        survey_bar: 'answer',
        nodeResource: mockJobTemplate,
        extra_data: { bar: 'answer' },
      },
      jtLaunchConfig
    );
  });

  test('Can successfully create a new project sync node', async () => {
    act(() => {
      wrapper.find('SelectableCard#link-type-failure').simulate('click');
    });
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('AnsibleSelect').prop('onChange')(null, 'project');
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('td#check-action-item-1').find('input').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        linkType: 'failure',
        nodeResource: {
          id: 1,
          name: 'Test Project',
          type: 'project',
          url: '/api/v2/projects/1',
        },
        nodeType: 'project',
        verbosity: undefined,
      },
      {}
    );
  });

  test('Can successfully create a new inventory source sync node', async () => {
    act(() => {
      wrapper.find('SelectableCard#link-type-failure').simulate('click');
    });
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('AnsibleSelect').prop('onChange')(null, 'inventory_source');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('td#check-action-item-1').find('input').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        linkType: 'failure',
        nodeResource: {
          id: 1,
          name: 'Test Inventory Source',
          type: 'inventory_source',
          url: '/api/v2/inventory_sources/1',
        },
        nodeType: 'inventory_source',
        verbosity: undefined,
      },
      {}
    );
  });

  test('Can successfully create a new workflow job template node', async () => {
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('AnsibleSelect').prop('onChange')(
        null,
        'workflow_job_template'
      );
    });
    wrapper.update();
    await act(async () =>
      wrapper.find('td#check-action-item-1').find('input').simulate('click')
    );
    wrapper.update();

    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        linkType: 'success',
        nodeResource: {
          id: 1,
          name: 'Test Workflow Job Template',
          type: 'workflow_job_template',
          url: '/api/v2/workflow_job_templates/1',
        },
        nodeType: 'workflow_job_template',
        verbosity: undefined,
      },
      {
        ask_inventory_on_launch: false,
        ask_limit_on_launch: false,
        ask_scm_branch_on_launch: false,
        ask_variables_on_launch: false,
        can_start_without_user_input: false,
        defaults: {
          extra_vars: '---',
          inventory: { id: null, name: null },
          limit: '',
          scm_branch: '',
        },
        node_prompts_rejected: [272, 273],
        node_templates_missing: [],
        survey_enabled: false,
        variables_needed_to_start: [],
        workflow_job_template_data: { description: '', id: 53, name: 'jt' },
      }
    );
  });

  test('Can successfully create a new approval template node', async () => {
    act(() => {
      wrapper.find('SelectableCard#link-type-always').simulate('click');
    });
    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('AnsibleSelect').prop('onChange')(
        null,
        'workflow_approval_template'
      );
    });
    wrapper.update();

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
      wrapper.find('input#approval-timeout-minutes').simulate('change', {
        target: { value: 5, name: 'timeoutMinutes' },
      });
      wrapper.find('input#approval-timeout-seconds').simulate('change', {
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
    expect(wrapper.find('input#approval-timeout-minutes').prop('value')).toBe(
      5
    );
    expect(wrapper.find('input#approval-timeout-seconds').prop('value')).toBe(
      30
    );

    await act(async () => {
      wrapper.find('button#next-node-modal').simulate('click');
    });
    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        approvalDescription: 'Test Approval Description',
        approvalName: 'Test Approval',
        linkType: 'always',
        nodeResource: null,
        nodeType: 'workflow_approval_template',
        timeoutMinutes: 5,
        timeoutSeconds: 30,
      },
      {}
    );
  });

  test('Cancel button dispatches as expected', () => {
    wrapper.find('button#cancel-node-modal').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'CANCEL_NODE_MODAL',
    });
  });
});
describe('Edit existing node', () => {
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
  let newWrapper;
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('Can successfully change project sync node to workflow approval node', async () => {
    await act(async () => {
      newWrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              nodeToEdit: {
                id: 2,
                identifier: 'Foo',
                fullUnifiedJobTemplate: {
                  id: 1,
                  name: 'Test Project',
                  type: 'project',
                },
              },
            }}
          >
            <NodeModal
              askLinkType={false}
              onSave={onSave}
              title="Edit Node"
              resourceDefaultCredentials={[]}
            />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });
    await waitForElement(newWrapper, 'PFWizard');
    newWrapper.update();
    expect(newWrapper.find('AnsibleSelect').prop('value')).toBe('project');
    await act(async () => {
      newWrapper.find('AnsibleSelect').prop('onChange')(
        null,
        'workflow_approval_template'
      );
    });
    newWrapper.update();
    await act(async () => {
      newWrapper.find('input#approval-name').simulate('change', {
        target: { value: 'Test Approval', name: 'approvalName' },
      });
      newWrapper.find('input#approval-description').simulate('change', {
        target: {
          value: 'Test Approval Description',
          name: 'approvalDescription',
        },
      });
      newWrapper.find('input#approval-timeout-minutes').simulate('change', {
        target: { value: 5, name: 'timeoutMinutes' },
      });
      newWrapper.find('input#approval-timeout-seconds').simulate('change', {
        target: { value: 30, name: 'timeoutSeconds' },
      });
    });
    newWrapper.update();

    expect(newWrapper.find('input#approval-name').prop('value')).toBe(
      'Test Approval'
    );
    expect(newWrapper.find('input#approval-description').prop('value')).toBe(
      'Test Approval Description'
    );
    expect(
      newWrapper.find('input#approval-timeout-minutes').prop('value')
    ).toBe(5);
    expect(
      newWrapper.find('input#approval-timeout-seconds').prop('value')
    ).toBe(30);
    await act(async () => {
      newWrapper.find('button#next-node-modal').simulate('click');
    });

    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        identifier: 'Foo',
        approvalDescription: 'Test Approval Description',
        approvalName: 'Test Approval',
        linkType: 'success',
        nodeResource: null,
        nodeType: 'workflow_approval_template',
        timeoutMinutes: 5,
        timeoutSeconds: 30,
      },
      {}
    );
  });

  test('Can successfully change approval node to workflow job template node', async () => {
    await act(async () => {
      newWrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              nodeToEdit: {
                id: 2,
                identifier: 'Foo',
                fullUnifiedJobTemplate: {
                  id: 1,
                  name: 'Test Approval',
                  description: 'Test Approval Description',
                  type: 'workflow_approval_template',
                  timeout: 0,
                },
              },
            }}
          >
            <NodeModal
              askLinkType={false}
              onSave={onSave}
              title="Edit Node"
              resourceDefaultCredentials={[]}
            />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });
    await waitForElement(newWrapper, 'PFWizard');
    expect(newWrapper.find('AnsibleSelect').prop('value')).toBe(
      'workflow_approval_template'
    );
    await act(async () => {
      newWrapper.find('AnsibleSelect').invoke('onChange')(
        null,
        'workflow_job_template'
      );
      newWrapper.update();
    });
    await waitForElement(newWrapper, 'WorkflowJobTemplatesList');
    expect(newWrapper.find('AnsibleSelect').prop('value')).toBe(
      'workflow_job_template'
    );
    await act(async () => {
      newWrapper.find('td#check-action-item-1').find('input').simulate('click');
      newWrapper.update();
    });
    newWrapper.update();
    await act(async () => {
      newWrapper.find('button#next-node-modal').simulate('click');
    });
    newWrapper.update();
    await act(async () => {
      newWrapper.find('button#next-node-modal').simulate('click');
    });
    expect(onSave).toBeCalledWith(
      {
        convergence: 'any',
        identifier: 'Foo',
        linkType: 'success',
        nodeResource: {
          id: 1,
          name: 'Test Workflow Job Template',
          type: 'workflow_job_template',
          url: '/api/v2/workflow_job_templates/1',
        },
        nodeType: 'workflow_job_template',
      },
      {
        ask_inventory_on_launch: false,
        ask_limit_on_launch: false,
        ask_scm_branch_on_launch: false,
        ask_variables_on_launch: false,
        can_start_without_user_input: false,
        defaults: {
          extra_vars: '---',
          inventory: { id: null, name: null },
          limit: '',
          scm_branch: '',
        },
        node_prompts_rejected: [272, 273],
        node_templates_missing: [],
        survey_enabled: false,
        variables_needed_to_start: [],
        workflow_job_template_data: { description: '', id: 53, name: 'jt' },
      }
    );
  });
});
