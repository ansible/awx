import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalListApproveButton from './WorkflowApprovalListApproveButton';

const workflowApproval = {
  id: 1,
  name: 'Foo',
  can_approve_or_deny: true,
  url: '/api/v2/workflow_approvals/218/',
};

describe('<WorkflowApprovalListApproveButton />', () => {
  test('should render button', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListApproveButton
        onApprove={() => {}}
        selectedItems={[]}
      />
    );
    expect(wrapper.find('button')).toHaveLength(1);
  });

  test('should invoke onApprove prop', () => {
    const onApprove = jest.fn();
    const wrapper = mountWithContexts(
      <WorkflowApprovalListApproveButton
        onApprove={onApprove}
        selectedItems={[workflowApproval]}
      />
    );
    wrapper.find('button').simulate('click');
    wrapper.update();
    expect(onApprove).toHaveBeenCalled();
  });

  test('should disable button when no approve/deny permissions', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListApproveButton
        onApprove={() => {}}
        selectedItems={[{ ...workflowApproval, can_approve_or_deny: false }]}
      />
    );
    expect(wrapper.find('button[disabled]')).toHaveLength(1);
  });

  test('should render tooltip', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListApproveButton
        onApprove={() => {}}
        selectedItems={[workflowApproval]}
      />
    );
    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Tooltip').prop('content')).toEqual('Approve');
  });
});
