import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalListDenyButton from './WorkflowApprovalListDenyButton';

const workflowApproval = {
  id: 1,
  name: 'Foo',
  can_approve_or_deny: true,
  url: '/api/v2/workflow_approvals/218/',
};

describe('<WorkflowApprovalListDenyButton />', () => {
  test('should render button', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListDenyButton onDeny={() => {}} selectedItems={[]} />
    );
    expect(wrapper.find('button')).toHaveLength(1);
  });

  test('should invoke onDeny prop', () => {
    const onDeny = jest.fn();
    const wrapper = mountWithContexts(
      <WorkflowApprovalListDenyButton
        onDeny={onDeny}
        selectedItems={[workflowApproval]}
      />
    );
    wrapper.find('button').simulate('click');
    wrapper.update();
    expect(onDeny).toHaveBeenCalled();
  });

  test('should disable button when no approve/deny permissions', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListDenyButton
        onDeny={() => {}}
        selectedItems={[{ ...workflowApproval, can_approve_or_deny: false }]}
      />
    );
    expect(wrapper.find('button[disabled]')).toHaveLength(1);
  });

  test('should render tooltip', () => {
    const wrapper = mountWithContexts(
      <WorkflowApprovalListDenyButton
        onDeny={() => {}}
        selectedItems={[workflowApproval]}
      />
    );
    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Tooltip').prop('content')).toEqual('Deny');
  });
});
