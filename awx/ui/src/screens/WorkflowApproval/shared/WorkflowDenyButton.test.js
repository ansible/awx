import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  shallowWithContexts,
} from '../../../../testUtils/enzymeHelpers';
import { WorkflowApprovalsAPI } from 'api';
import WorkflowDenyButton from './WorkflowDenyButton';
import mockData from '../data.workflowApprovals.json';

jest.mock('api');

describe('<WorkflowDenyButton/> shallow mount', () => {
  let wrapper;

  let mockApprovalList = mockData.results;

  test('initially render successfully', () => {
    wrapper = shallowWithContexts(
      <WorkflowDenyButton workflowApproval={mockApprovalList[0]} />
    );

    expect(wrapper.find('WorkflowDenyButton')).toHaveLength(1);
    wrapper
      .find('Button')
      .forEach((button) => expect(button.prop('isDisabled')).toBe(false));
  });
});

describe('<WorkflowDenyButton/>, full mount', () => {
  let wrapper;
  let mockApprovalList = mockData.results;
  const denyButton = 'Button[ouiaId="workflow-deny-button"]';
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should be disabled', () => {
    wrapper = mountWithContexts(
      <WorkflowDenyButton
        workflowApproval={mockApprovalList[2]}
        onHandleToast={jest.fn()}
      />
    );
    expect(wrapper.find(denyButton)).toHaveLength(1);
    expect(wrapper.find(denyButton).prop('isDisabled')).toBe(true);
  });

  test('should handle deny', async () => {
    act(() => {
      wrapper = mountWithContexts(
        <WorkflowDenyButton
          workflowApproval={mockApprovalList[0]}
          onHandleToast={jest.fn()}
        />
      );
    });
    await act(() => wrapper.find(denyButton).prop('onClick')());
    expect(WorkflowApprovalsAPI.deny).toBeCalledWith(218);
  });

  test('Should handle deny error', async () => {
    WorkflowApprovalsAPI.deny.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/workflow',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    act(() => {
      wrapper = mountWithContexts(
        <WorkflowDenyButton
          workflowApproval={mockApprovalList[0]}
          onHandleToast={jest.fn()}
        />
      );
    });
    await act(() => wrapper.find(denyButton).prop('onClick')());
    wrapper.update();
    expect(wrapper.find('ErrorDetail')).toHaveLength(1);
  });
});
