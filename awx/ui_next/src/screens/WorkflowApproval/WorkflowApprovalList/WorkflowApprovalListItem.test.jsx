import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalListItem from './WorkflowApprovalListItem';
import mockWorkflowApprovals from '../data.workflowApprovals.json';

const workflowApproval = mockWorkflowApprovals.results[0];

jest.mock('../../../api/models/WorkflowApprovals');

describe('<WorkflowApprovalListItem />', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });

  test('should display never expires status', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <WorkflowApprovalListItem
            isSelected={false}
            detailUrl={`/workflow_approvals/${workflowApproval.id}`}
            onSelect={() => {}}
            workflowApproval={workflowApproval}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Label[children="Never expires"]').length).toBe(1);
  });
  test('should display timed out status', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <WorkflowApprovalListItem
            isSelected={false}
            detailUrl={`/workflow_approvals/${workflowApproval.id}`}
            onSelect={() => {}}
            workflowApproval={{
              ...workflowApproval,
              status: 'failed',
              timed_out: true,
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Label[children="Timed out"]').length).toBe(1);
  });
  test('should display canceled status', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <WorkflowApprovalListItem
            isSelected={false}
            detailUrl={`/workflow_approvals/${workflowApproval.id}`}
            onSelect={() => {}}
            workflowApproval={{
              ...workflowApproval,
              canceled_on: '2020-10-09T19:59:26.974046Z',
              status: 'canceled',
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Label[children="Canceled"]').length).toBe(1);
  });
  test('should display approved status', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <WorkflowApprovalListItem
            isSelected={false}
            detailUrl={`/workflow_approvals/${workflowApproval.id}`}
            onSelect={() => {}}
            workflowApproval={{
              ...workflowApproval,
              status: 'successful',
              summary_fields: {
                ...workflowApproval.summary_fields,
                approved_or_denied_by: {
                  id: 1,
                  username: 'admin',
                  first_name: '',
                  last_name: '',
                },
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Label[children="Approved"]').length).toBe(1);
  });
  test('should display denied status', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <WorkflowApprovalListItem
            isSelected={false}
            detailUrl={`/workflow_approvals/${workflowApproval.id}`}
            onSelect={() => {}}
            workflowApproval={{
              ...workflowApproval,
              failed: true,
              status: 'failed',
              summary_fields: {
                ...workflowApproval.summary_fields,
                approved_or_denied_by: {
                  id: 1,
                  username: 'admin',
                  first_name: '',
                  last_name: '',
                },
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Label[children="Denied"]').length).toBe(1);
  });
});
