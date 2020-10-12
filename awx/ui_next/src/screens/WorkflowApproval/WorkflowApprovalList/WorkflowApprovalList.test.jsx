import React from 'react';
import { act } from 'react-dom/test-utils';
import { WorkflowApprovalsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalList from './WorkflowApprovalList';

jest.mock('../../../api');

const mockWorkflowApprovals = [
  {
    id: 221,
    type: 'workflow_approval',
    url: '/api/v2/workflow_approvals/221/',
    related: {
      created_by: '/api/v2/users/1/',
      unified_job_template: '/api/v2/workflow_approval_templates/10/',
      source_workflow_job: '/api/v2/workflow_jobs/220/',
      workflow_approval_template: '/api/v2/workflow_approval_templates/10/',
      approve: '/api/v2/workflow_approvals/221/approve/',
      deny: '/api/v2/workflow_approvals/221/deny/',
    },
    summary_fields: {
      workflow_job_template: {
        id: 9,
        name: 'Approval @ 9:15:26 AM',
        description: '',
      },
      workflow_job: {
        id: 220,
        name: 'Approval @ 9:15:26 AM',
        description: '',
      },
      workflow_approval_template: {
        id: 10,
        name: 'approval copy',
        description: '',
        timeout: 30,
      },
      unified_job_template: {
        id: 10,
        name: 'approval copy',
        description: '',
        unified_job_type: 'workflow_approval',
      },
      created_by: {
        id: 1,
        username: 'admin',
        first_name: '',
        last_name: '',
      },
      user_capabilities: {
        delete: true,
        start: true,
      },
      source_workflow_job: {
        id: 220,
        name: 'Approval @ 9:15:26 AM',
        description: '',
        status: 'failed',
        failed: true,
        elapsed: 89.766,
      },
    },
    created: '2020-10-09T19:58:27.337904Z',
    modified: '2020-10-09T19:58:27.338000Z',
    name: 'approval copy',
    description: '',
    unified_job_template: 10,
    launch_type: 'workflow',
    status: 'failed',
    failed: true,
    started: '2020-10-09T19:58:27.337904Z',
    finished: '2020-10-09T19:59:26.974046Z',
    canceled_on: null,
    elapsed: 59.636,
    job_explanation:
      'The approval node approval copy (221) has expired after 30 seconds.',
    can_approve_or_deny: false,
    approval_expiration: null,
    timed_out: true,
  },
  {
    id: 6,
    type: 'workflow_approval',
    url: '/api/v2/workflow_approvals/6/',
    related: {
      created_by: '/api/v2/users/1/',
      unified_job_template: '/api/v2/workflow_approval_templates/8/',
      source_workflow_job: '/api/v2/workflow_jobs/5/',
      workflow_approval_template: '/api/v2/workflow_approval_templates/8/',
      approve: '/api/v2/workflow_approvals/6/approve/',
      deny: '/api/v2/workflow_approvals/6/deny/',
      approved_or_denied_by: '/api/v2/users/1/',
    },
    summary_fields: {
      workflow_job_template: {
        id: 7,
        name: 'Approval',
        description: '',
      },
      workflow_job: {
        id: 5,
        name: 'Approval',
        description: '',
      },
      workflow_approval_template: {
        id: 8,
        name: 'approval',
        description: '',
        timeout: 0,
      },
      unified_job_template: {
        id: 8,
        name: 'approval',
        description: '',
        unified_job_type: 'workflow_approval',
      },
      approved_or_denied_by: {
        id: 1,
        username: 'admin',
        first_name: '',
        last_name: '',
      },
      created_by: {
        id: 1,
        username: 'admin',
        first_name: '',
        last_name: '',
      },
      user_capabilities: {
        delete: false,
        start: false,
      },
      source_workflow_job: {
        id: 5,
        name: 'Approval',
        description: '',
        status: 'successful',
        failed: false,
        elapsed: 168.233,
      },
    },
    created: '2020-10-05T20:14:53.875701Z',
    modified: '2020-10-05T20:17:41.211373Z',
    name: 'approval',
    description: '',
    unified_job_template: 8,
    launch_type: 'workflow',
    status: 'successful',
    failed: false,
    started: '2020-10-05T20:14:53.875701Z',
    finished: '2020-10-05T20:17:41.200738Z',
    canceled_on: null,
    elapsed: 167.325,
    job_explanation: '',
    can_approve_or_deny: false,
    approval_expiration: null,
    timed_out: false,
  },
];

describe('<WorkflowApprovalList />', () => {
  let wrapper;
  beforeEach(() => {
    WorkflowApprovalsAPI.read.mockResolvedValue({
      data: {
        count: mockWorkflowApprovals.length,
        results: mockWorkflowApprovals,
      },
    });

    WorkflowApprovalsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should load and render workflow approvals', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    expect(wrapper.find('WorkflowApprovalListItem')).toHaveLength(2);
  });

  test('should select workflow approval when checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(
      wrapper
        .find('WorkflowApprovalListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should select all', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();

    const items = wrapper.find('WorkflowApprovalListItem');
    expect(items).toHaveLength(2);
    items.forEach(item => {
      expect(item.prop('isSelected')).toEqual(true);
    });

    expect(
      wrapper
        .find('WorkflowApprovalListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should disable delete button', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(wrapper.find('ToolbarDeleteButton button').prop('disabled')).toEqual(
      true
    );
  });

  test('should call delete api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(WorkflowApprovalsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show deletion error', async () => {
    WorkflowApprovalsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/workflow_approvals/221',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();
    expect(WorkflowApprovalsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();

    const modal = wrapper.find('Modal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });
});
