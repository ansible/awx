import React from 'react';

import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalListItem from './WorkflowApprovalListItem';
import { WorkflowApprovalsAPI } from '../../../api';
import workflowApproval from '../data.workflowApproval.json';

jest.mock('../../../api/models/WorkflowApprovals');

describe('<WorkflowApprovalListItem />', () => {
  test('action buttons shown to users with ability to approve/deny', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListItem
        isSelected={false}
        detailUrl={`/workflow_approvals/${workflowApproval.id}`}
        onSelect={() => {}}
        workflowApproval={workflowApproval}
      />
    );
    expect(wrapper.find('WorkflowApprovalActionButtons').exists()).toBeTruthy();
  });

  test('action buttons hidden from users without ability to approve/deny', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListItem
        isSelected={false}
        detailUrl={`/workflow_approvals/${workflowApproval.id}`}
        onSelect={() => {}}
        workflowApproval={{ ...workflowApproval, can_approve_or_deny: false }}
      />
    );
    expect(wrapper.find('WorkflowApprovalActionButtons').exists()).toBeFalsy();
  });

  test('should hide action buttons after successful action', async () => {
    WorkflowApprovalsAPI.approve.mockResolvedValue();
    const wrapper = mountWithContexts(
      <WorkflowApprovalListItem
        isSelected={false}
        detailUrl={`/workflow_approvals/${workflowApproval.id}`}
        onSelect={() => {}}
        workflowApproval={workflowApproval}
      />
    );
    expect(wrapper.find('WorkflowApprovalActionButtons').exists()).toBeTruthy();
    await act(async () =>
      wrapper.find('Button[aria-label="Approve"]').prop('onClick')()
    );
    wrapper.update();
    expect(WorkflowApprovalsAPI.approve).toHaveBeenCalled();
    expect(wrapper.find('WorkflowApprovalActionButtons').exists()).toBeFalsy();
    jest.clearAllMocks();
  });
});
