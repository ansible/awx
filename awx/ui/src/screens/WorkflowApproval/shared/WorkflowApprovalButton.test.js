import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  shallowWithContexts,
} from '../../../../testUtils/enzymeHelpers';
import { WorkflowApprovalsAPI } from 'api';
import WorkflowApprovalButton from './WorkflowApprovalButton';
import mockData from '../data.workflowApprovals.json';

jest.mock('api');

describe('<WorkflowApprovalButton/> shallow mount', () => {
  let wrapper;

  let mockApprovalList = mockData.results;

  test('initially render successfully', () => {
    wrapper = shallowWithContexts(
      <WorkflowApprovalButton
        workflowApproval={mockApprovalList[0]}
        onHandleToast={jest.fn()}
      />
    );

    expect(wrapper.find('WorkflowApprovalButton')).toHaveLength(1);
    wrapper
      .find('Button')
      .forEach((button) => expect(button.prop('isDisabled')).toBe(false));
  });
});

describe('<WorkflowApprovalButton/>, full mount', () => {
  let wrapper;
  let mockApprovalList = mockData.results;
  const approveButton = 'Button[ouiaId="workflow-approve-button"]';
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should be disabled', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalButton
        workflowApproval={mockApprovalList[2]}
        onHandleToast={jest.fn()}
      />
    );
    expect(wrapper.find(approveButton)).toHaveLength(1);
    expect(wrapper.find(approveButton).prop('isDisabled')).toBe(true);
  });
  test('should handle approve', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <WorkflowApprovalButton
          workflowApproval={mockApprovalList[0]}
          onHandleToast={jest.fn()}
        />
      );
    });
    await act(() => wrapper.find(approveButton).prop('onClick')());
    expect(WorkflowApprovalsAPI.approve).toBeCalledWith(218);
  });
});
