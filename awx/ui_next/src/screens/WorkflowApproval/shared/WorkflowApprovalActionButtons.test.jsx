import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { WorkflowApprovalsAPI } from '../../../api';
import WorkflowApprovalActionButtons from './WorkflowApprovalActionButtons';
import workflowApproval from '../data.workflowApproval.json';

jest.mock('../../../api/models/WorkflowApprovals');

describe('<WorkflowApprovalActionButtons />', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders succesfully with icons', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalActionButtons workflowApproval={workflowApproval} />
    );
    expect(wrapper.find('CheckIcon').length).toBe(1);
    expect(wrapper.find('CloseIcon').length).toBe(1);
    expect(wrapper.find('Button[children="Approve"]').length).toBe(0);
    expect(wrapper.find('Button[children="Deny"]').length).toBe(0);
  });
  test('initially renders succesfully without icons', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalActionButtons
        workflowApproval={workflowApproval}
        icon={false}
      />
    );
    expect(wrapper.find('CheckIcon').length).toBe(0);
    expect(wrapper.find('CloseIcon').length).toBe(0);
    expect(wrapper.find('Button[children="Approve"]').length).toBe(1);
    expect(wrapper.find('Button[children="Deny"]').length).toBe(1);
  });
  test('approving makes correct call with correct param', async () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalActionButtons workflowApproval={workflowApproval} />
    );
    await act(async () => wrapper.find('CheckIcon').simulate('click'));
    expect(WorkflowApprovalsAPI.approve).toHaveBeenCalledWith(
      workflowApproval.id
    );
  });
  test('denying makes correct call with correct param', async () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalActionButtons workflowApproval={workflowApproval} />
    );
    await act(async () => wrapper.find('CloseIcon').simulate('click'));
    expect(WorkflowApprovalsAPI.deny).toHaveBeenCalledWith(workflowApproval.id);
  });
  test('approval error shown', async () => {
    WorkflowApprovalsAPI.approve.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/workflow_approvals/approve',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    wrapper = mountWithContexts(
      <WorkflowApprovalActionButtons workflowApproval={workflowApproval} />
    );
    expect(wrapper.find('AlertModal').length).toBe(0);
    await act(async () => wrapper.find('CheckIcon').simulate('click'));
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
  });
  test('denial error shown', async () => {
    WorkflowApprovalsAPI.deny.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/workflow_approvals/deny',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    wrapper = mountWithContexts(
      <WorkflowApprovalActionButtons workflowApproval={workflowApproval} />
    );
    expect(wrapper.find('AlertModal').length).toBe(0);
    await act(async () => wrapper.find('CloseIcon').simulate('click'));
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
  });
});
