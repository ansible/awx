import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { formatDateString } from '../../../util/dates';
import WorkflowApprovalStatus from './WorkflowApprovalStatus';
import mockWorkflowApprovals from '../data.workflowApprovals.json';

const workflowApproval = mockWorkflowApprovals.results[0];

describe('<WorkflowApprovalStatus />', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('shows no expiration when approval status is pending and no approval_expiration', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalStatus workflowApproval={workflowApproval} />
    );
    expect(wrapper.text()).toBe('Never expires');
  });
  test('shows expiration date/time when approval status is pending and approval_expiration present', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalStatus
        workflowApproval={{
          ...workflowApproval,
          approval_expiration: '2020-10-10T17:13:12.067947Z',
        }}
      />
    );
    expect(wrapper.text()).toBe(
      `Expires on ${formatDateString('2020-10-10T17:13:12.067947Z')}`
    );
  });
  test('shows when an approval has timed out', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalStatus
        workflowApproval={{
          ...workflowApproval,
          status: 'failed',
          timed_out: true,
        }}
      />
    );
    expect(wrapper.find('Label').text()).toBe('Timed out');
  });
  test('shows when an approval has canceled', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalStatus
        workflowApproval={{
          ...workflowApproval,
          status: 'canceled',
          canceled_on: '2020-10-10T17:13:12.067947Z',
        }}
      />
    );
    expect(wrapper.find('Label').text()).toBe('Canceled');
  });
  test('shows when an approval has approved', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalStatus
        workflowApproval={{
          ...workflowApproval,
          summary_fields: {
            ...workflowApproval.summary_fields,
            approved_or_denied_by: {
              id: 1,
              username: 'Foobar',
            },
          },
          status: 'successful',
          finished: '2020-10-10T17:13:12.067947Z',
        }}
      />
    );
    expect(wrapper.find('Label').text()).toBe('Approved');
  });
  test('shows when an approval has denied', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalStatus
        workflowApproval={{
          ...workflowApproval,
          summary_fields: {
            ...workflowApproval.summary_fields,
            approved_or_denied_by: {
              id: 1,
              username: 'Foobar',
            },
          },
          status: 'failed',
          finished: '2020-10-10T17:13:12.067947Z',
          failed: true,
        }}
      />
    );
    expect(wrapper.find('Label').text()).toBe('Denied');
  });
});
