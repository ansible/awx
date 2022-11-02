import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowApprovalsAPI,
  WorkflowJobTemplatesAPI,
  WorkflowJobsAPI,
} from 'api';
import { formatDateString } from 'util/dates';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalDetail from './WorkflowApprovalDetail';
import mockWorkflowApprovals from '../data.workflowApprovals.json';

const workflowApproval = mockWorkflowApprovals.results[0];

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 218,
  }),
}));

const workflowJobTemplate = {
  id: 8,
  type: 'workflow_job_template',
  url: '/api/v2/workflow_job_templates/8/',
  related: {
    named_url: '/api/v2/workflow_job_templates/00++/',
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    last_job: '/api/v2/workflow_jobs/111/',
    workflow_jobs: '/api/v2/workflow_job_templates/8/workflow_jobs/',
    schedules: '/api/v2/workflow_job_templates/8/schedules/',
    launch: '/api/v2/workflow_job_templates/8/launch/',
    webhook_key: '/api/v2/workflow_job_templates/8/webhook_key/',
    webhook_receiver: '/api/v2/workflow_job_templates/8/github/',
    workflow_nodes: '/api/v2/workflow_job_templates/8/workflow_nodes/',
    labels: '/api/v2/workflow_job_templates/8/labels/',
    activity_stream: '/api/v2/workflow_job_templates/8/activity_stream/',
    notification_templates_started:
      '/api/v2/workflow_job_templates/8/notification_templates_started/',
    notification_templates_success:
      '/api/v2/workflow_job_templates/8/notification_templates_success/',
    notification_templates_error:
      '/api/v2/workflow_job_templates/8/notification_templates_error/',
    notification_templates_approvals:
      '/api/v2/workflow_job_templates/8/notification_templates_approvals/',
    access_list: '/api/v2/workflow_job_templates/8/access_list/',
    object_roles: '/api/v2/workflow_job_templates/8/object_roles/',
    survey_spec: '/api/v2/workflow_job_templates/8/survey_spec/',
    copy: '/api/v2/workflow_job_templates/8/copy/',
  },
  summary_fields: {
    last_job: {
      id: 111,
      name: '00',
      description: '',
      finished: '2022-05-10T17:29:52.978531Z',
      status: 'successful',
      failed: false,
    },
    last_update: {
      id: 111,
      name: '00',
      description: '',
      status: 'successful',
      failed: false,
    },
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    object_roles: {
      admin_role: {
        description: 'Can manage all aspects of the workflow job template',
        name: 'Admin',
        id: 34,
      },
      execute_role: {
        description: 'May run the workflow job template',
        name: 'Execute',
        id: 35,
      },
      read_role: {
        description: 'May view settings for the workflow job template',
        name: 'Read',
        id: 36,
      },
      approval_role: {
        description: 'Can approve or deny a workflow approval node',
        name: 'Approve',
        id: 37,
      },
    },
    user_capabilities: {
      edit: true,
      delete: true,
      start: true,
      schedule: true,
      copy: true,
    },
    labels: {
      count: 1,
      results: [
        {
          id: 2,
          name: 'Test2',
        },
      ],
    },
    survey: {
      title: '',
      description: '',
    },
    recent_jobs: [
      {
        id: 111,
        status: 'successful',
        finished: '2022-05-10T17:29:52.978531Z',
        canceled_on: null,
        type: 'workflow_job',
      },
      {
        id: 104,
        status: 'failed',
        finished: '2022-05-10T15:26:22.233170Z',
        canceled_on: null,
        type: 'workflow_job',
      },
    ],
  },
  created: '2022-05-05T14:13:36.123027Z',
  modified: '2022-05-05T17:44:44.071447Z',
  name: '00',
  description: '',
  last_job_run: '2022-05-10T17:29:52.978531Z',
  last_job_failed: false,
  next_job_run: null,
  status: 'successful',
  extra_vars: '{\n  "foo": "bar",\n  "baz": "qux"\n}',
  organization: null,
  survey_enabled: true,
  allow_simultaneous: true,
  ask_variables_on_launch: true,
  inventory: null,
  limit: null,
  scm_branch: '',
  ask_inventory_on_launch: true,
  ask_scm_branch_on_launch: true,
  ask_limit_on_launch: true,
  webhook_service: 'github',
  webhook_credential: null,
};

const workflowJob = {
  id: 111,
  type: 'workflow_job',
  url: '/api/v2/workflow_jobs/111/',
  related: {
    created_by: '/api/v2/users/1/',
    modified_by: '/api/v2/users/1/',
    unified_job_template: '/api/v2/workflow_job_templates/8/',
    workflow_job_template: '/api/v2/workflow_job_templates/8/',
    notifications: '/api/v2/workflow_jobs/111/notifications/',
    workflow_nodes: '/api/v2/workflow_jobs/111/workflow_nodes/',
    labels: '/api/v2/workflow_jobs/111/labels/',
    activity_stream: '/api/v2/workflow_jobs/111/activity_stream/',
    relaunch: '/api/v2/workflow_jobs/111/relaunch/',
    cancel: '/api/v2/workflow_jobs/111/cancel/',
  },
  summary_fields: {
    inventory: {
      id: 1,
      name: 'Demo Inventory',
      description: '',
      has_active_failures: false,
      total_hosts: 2,
      hosts_with_active_failures: 0,
      total_groups: 0,
      has_inventory_sources: false,
      total_inventory_sources: 0,
      inventory_sources_with_failures: 0,
      organization_id: 1,
      kind: '',
    },
    workflow_job_template: {
      id: 8,
      name: '00',
      description: '',
    },
    unified_job_template: {
      id: 8,
      name: '00',
      description: '',
      unified_job_type: 'workflow_job',
    },
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    user_capabilities: {
      delete: true,
      start: true,
    },
    labels: {
      count: 1,
      results: [
        {
          id: 2,
          name: 'Test2',
        },
      ],
    },
  },
  created: '2022-05-10T15:26:45.730965Z',
  modified: '2022-05-10T15:26:46.150107Z',
  name: '00',
  description: '',
  unified_job_template: 8,
  launch_type: 'manual',
  status: 'successful',
  failed: false,
  started: '2022-05-10T15:26:46.149825Z',
  finished: '2022-05-10T17:29:52.978531Z',
  canceled_on: null,
  elapsed: 7386.829,
  job_args: '',
  job_cwd: '',
  job_env: {},
  job_explanation: '',
  result_traceback: '',
  launched_by: {
    id: 1,
    name: 'admin',
    type: 'user',
    url: '/api/v2/users/1/',
  },
  work_unit_id: null,
  workflow_job_template: 8,
  extra_vars: '{"foo": "bar", "baz": "qux", "first_one": 10}',
  allow_simultaneous: true,
  job_template: null,
  is_sliced_job: false,
  inventory: 1,
  limit: 'localhost',
  scm_branch: 'main',
  webhook_service: '',
  webhook_credential: null,
  webhook_guid: '',
};

describe('<WorkflowApprovalDetail />', () => {
  beforeEach(() => {
    WorkflowJobTemplatesAPI.readDetail.mockResolvedValue({
      data: workflowJobTemplate,
    });
    WorkflowJobsAPI.readDetail.mockResolvedValue({ data: workflowJob });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render Details', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail workflowApproval={workflowApproval} />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Name', workflowApproval.name);
    assertDetail('Description', workflowApproval.description);
    assertDetail('Expires', 'Never');
    assertDetail(
      'Workflow Job',
      `${workflowApproval.summary_fields.workflow_job.id} - ${workflowApproval.summary_fields.workflow_job.name}`
    );
    assertDetail(
      'Workflow Job Template',
      workflowApproval.summary_fields.workflow_job_template.name
    );
    const dateDetails = wrapper.find('UserDateDetail');
    expect(dateDetails).toHaveLength(1);
    expect(dateDetails.at(0).prop('label')).toEqual('Created');
    expect(dateDetails.at(0).prop('date')).toEqual(
      '2020-10-09T17:13:12.067947Z'
    );
    expect(dateDetails.at(0).prop('user')).toEqual(
      workflowApproval.summary_fields.created_by
    );
    assertDetail('Last Modified', formatDateString(workflowApproval.modified));
    assertDetail('Elapsed', '00:00:22');
    assertDetail('Limit', 'localhost');
    assertDetail('Source Control Branch', 'main');
    const linkInventory = wrapper
      .find('Detail[label="Inventory"]')
      .find('Link');
    expect(linkInventory.prop('to')).toEqual(
      '/inventories/inventory/1/details'
    );
    assertDetail('Labels', 'Test2');
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '{"foo": "bar", "baz": "qux", "first_one": 10}'
    );
  });

  test('should show expiration date/time', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            approval_expiration: '2020-10-10T17:13:12.067947Z',
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find(`Detail[label="Expires"] dd`).text()).toBe(
      `${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });

  test('should show finished date/time', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            finished: '2020-10-10T17:13:12.067947Z',
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find(`Detail[label="Finished"] dd`).text()).toBe(
      `${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });

  test('should show canceled date/time', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            canceled_on: '2020-10-10T17:13:12.067947Z',
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);

    expect(wrapper.find(`Detail[label="Canceled"] dd`).text()).toBe(
      `${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });

  test('should show explanation', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            job_explanation: 'Some explanation text',
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find(`Detail[label="Explanation"] dd`).text()).toBe(
      'Some explanation text'
    );
  });

  test('should show status when not pending', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            status: 'successful',
            summary_fields: {
              ...workflowApproval.summary_fields,
              approved_or_denied_by: {
                id: 1,
                username: 'Foobar',
              },
            },
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find('StatusLabel').text()).toBe('Approved');
  });

  test('should show actor when available', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            summary_fields: {
              ...workflowApproval.summary_fields,
              approved_or_denied_by: {
                id: 1,
                username: 'Foobar',
              },
            },
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find(`Detail[label="Actor"] dd`).text()).toBe('Foobar');
  });

  test('action buttons should be hidden when user cannot approve or deny', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            can_approve_or_deny: false,
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find('WorkflowApprovalActionButtons').length).toBe(0);
  });

  test('only the delete button should render when approval is not pending', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            can_approve_or_deny: true,
            status: 'successful',
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    expect(wrapper.find('WorkflowApprovalControls').length).toBe(0);
    expect(wrapper.find('Button[aria-label="Approve"]').length).toBe(0);
    expect(wrapper.find('DeleteButton').length).toBe(1);
  });

  test('should not load Labels', async () => {
    WorkflowJobTemplatesAPI.readDetail.mockResolvedValue({
      data: workflowJobTemplate,
    });
    WorkflowJobsAPI.readDetail.mockResolvedValue({
      data: {
        ...workflowApproval,
        summary_fields: {
          ...workflowApproval.summary_fields,
          labels: {
            results: [],
          },
        },
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail workflowApproval={workflowApproval} />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    const labels_detail = wrapper.find(`Detail[label="Labels"]`).at(0);
    expect(labels_detail.prop('isEmpty')).toEqual(true);
  });

  test('Error dialog shown for failed approval', async () => {
    WorkflowApprovalsAPI.approve.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={workflowApproval}
          fetchWorkflowApproval={jest.fn()}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    await act(async () => {
      wrapper
        .find('Button[ouiaId="workflow-approve-button"]')
        .at(0)
        .invoke('onClick')();
    });
    expect(WorkflowApprovalsAPI.approve).toHaveBeenCalledTimes(1);
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 0
    );
  });

  test('Error dialog shown for failed denial', async () => {
    WorkflowApprovalsAPI.deny.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={workflowApproval}
          fetchWorkflowApproval={jest.fn()}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    await act(async () => {
      wrapper.find('Button[ouiaId="workflow-deny-button"]').invoke('onClick')();
    });
    expect(WorkflowApprovalsAPI.deny).toHaveBeenCalledTimes(1);
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 0
    );
  });

  test('Error dialog shown for failed deletion', async () => {
    WorkflowApprovalsAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApprovalDetail
          workflowApproval={{
            ...workflowApproval,
            status: 'successful',
            summary_fields: {
              ...workflowApproval.summary_fields,
              approved_or_denied_by: {
                id: 1,
                username: 'Foobar',
              },
            },
          }}
        />
      );
    });
    waitForElement(wrapper, 'WorkflowApprovalDetail', (el) => el.length > 0);
    await waitForElement(
      wrapper,
      'WorkflowApprovalDetail Button[aria-label="Delete"]'
    );
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 0
    );
  });
});
