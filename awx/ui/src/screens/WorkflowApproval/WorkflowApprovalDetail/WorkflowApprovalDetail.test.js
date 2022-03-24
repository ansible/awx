import React from 'react';
import { act } from 'react-dom/test-utils';
import { WorkflowApprovalsAPI } from 'api';
import { formatDateString } from 'util/dates';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalDetail from './WorkflowApprovalDetail';
import mockWorkflowApprovals from '../data.workflowApprovals.json';

const workflowApproval = mockWorkflowApprovals.results[0];

jest.mock('../../../api');

describe('<WorkflowApprovalDetail />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(
      <WorkflowApprovalDetail workflowApproval={workflowApproval} />
    );
  });

  test('should render Details', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail workflowApproval={workflowApproval} />
    );
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
    expect(wrapper.find('WorkflowApprovalControls').length).toBe(1);
  });

  test('should show expiration date/time', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          approval_expiration: '2020-10-10T17:13:12.067947Z',
        }}
      />
    );
    expect(wrapper.find(`Detail[label="Expires"] dd`).text()).toBe(
      `${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });

  test('should show finished date/time', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          finished: '2020-10-10T17:13:12.067947Z',
        }}
      />
    );
    expect(wrapper.find(`Detail[label="Finished"] dd`).text()).toBe(
      `${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });

  test('should show canceled date/time', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          canceled_on: '2020-10-10T17:13:12.067947Z',
        }}
      />
    );
    expect(wrapper.find(`Detail[label="Canceled"] dd`).text()).toBe(
      `${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });

  test('should show explanation', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          job_explanation: 'Some explanation text',
        }}
      />
    );
    expect(wrapper.find(`Detail[label="Explanation"] dd`).text()).toBe(
      'Some explanation text'
    );
  });

  test('should show status when not pending', () => {
    const wrapper = mountWithContexts(
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
    expect(wrapper.find('StatusLabel').text()).toBe('Approved');
  });

  test('should show actor when available', () => {
    const wrapper = mountWithContexts(
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
    expect(wrapper.find(`Detail[label="Actor"] dd`).text()).toBe('Foobar');
  });

  test('action buttons should be hidden when user cannot approve or deny', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          can_approve_or_deny: false,
        }}
      />
    );
    expect(wrapper.find('WorkflowApprovalActionButtons').length).toBe(0);
  });
  test('only the delete button should render when approval is not pending', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          can_approve_or_deny: true,
          status: 'successful',
        }}
      />
    );
    expect(wrapper.find('WorkflowApprovalControls').length).toBe(0);
    expect(wrapper.find('Button[aria-label="Approve"]').length).toBe(0);
    expect(wrapper.find('DeleteButton').length).toBe(1);
  });

  test('Error dialog shown for failed approval', async () => {
    WorkflowApprovalsAPI.approve.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail workflowApproval={workflowApproval} />
    );
    await act(async () => {
      wrapper.find('DropdownToggleAction').invoke('onClick')();
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
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail workflowApproval={workflowApproval} />
    );
    await act(async () => wrapper.find('Toggle').prop('onToggle')(true));
    wrapper.update();
    await waitForElement(
      wrapper,
      'WorkflowApprovalDetail DropdownItem[ouiaId="workflow-deny-button"]'
    );
    await act(async () => {
      wrapper
        .find('DropdownItem[ouiaId="workflow-deny-button"]')
        .invoke('onClick')();
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

  test('delete button should be hidden when user cannot delete', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          status: 'successful',
          summary_fields: {
            ...workflowApproval.summary_fields,
            user_capabilities: {
              delete: false,
              start: false,
            },
            approved_or_denied_by: {
              id: 1,
              username: 'Foobar',
            },
          },
        }}
      />
    );
    expect(wrapper.find('DeleteButton').length).toBe(0);
  });

  test('delete button should be hidden when job is pending and approve, action buttons should render', async () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={{
          ...workflowApproval,
          summary_fields: {
            ...workflowApproval.summary_fields,
            user_capabilities: {
              delete: true,
              start: false,
            },
          },
          can_approve_or_deny: true,
        }}
      />
    );

    expect(wrapper.find('DeleteButton').length).toBe(0);
    expect(wrapper.find('WorkflowApprovalControls').length).toBe(1);
    await act(async () => wrapper.find('Toggle').prop('onToggle')(true));
    wrapper.update();

    const denyItem = wrapper.find(
      'DropdownItem[ouiaId="workflow-deny-button"]'
    );
    const cancelItem = wrapper.find(
      'DropdownItem[ouiaId="workflow-cancel-button"]'
    );
    expect(denyItem).toHaveLength(1);
    expect(denyItem.prop('description')).toBe(
      'This will continue the workflow along failure and always paths.'
    );
    expect(cancelItem).toHaveLength(1);
    expect(cancelItem.prop('description')).toBe(
      'This will cancel the workflow and no subsequent nodes will execute.'
    );
    expect(
      wrapper.find('DropdownItem[ouiaId="workflow-delete-button"]')
    ).toHaveLength(0);
  });

  test('Delete button is visible and approve action is not', async () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalDetail
        workflowApproval={mockWorkflowApprovals.results[1]}
      />
    );
    expect(wrapper.find('DeleteButton').length).toBe(1);
    expect(wrapper.find('DeleteButton').prop('isDisabled')).toBe(false);
    expect(wrapper.find('WorkflowApprovalControls').length).toBe(0);
  });

  test('Error dialog shown for failed deletion', async () => {
    WorkflowApprovalsAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    const wrapper = mountWithContexts(
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
