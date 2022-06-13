import React from 'react';

import {
  mountWithContexts,
  shallowWithContexts,
} from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalControls from './WorkflowApprovalControls';
import mockData from '../data.workflowApprovals.json';

describe('<WorkflowApprovalControls/> shallow mount', () => {
  let wrapper;
  let onHandleDeny = jest.fn();
  let onHandleCancel = jest.fn();
  let onHandleToggleToolbarKebab = jest.fn();
  let mockApprovalList = mockData.results;

  test('initially render successfully', () => {
    wrapper = shallowWithContexts(
      <WorkflowApprovalControls
        selected={[]}
        onHandleDeny={onHandleDeny}
        onHandleCancel={onHandleCancel}
        onHandleToggleToolbarKebab={onHandleToggleToolbarKebab}
        isKebabOpen={false}
      />
    );
    expect(wrapper.find('WorkflowApprovalControls')).toHaveLength(1);
    expect(wrapper.find('WorkflowApprovalControls').prop('isKebabOpen')).toBe(
      false
    );
  });
  test('is open with the correct dropdown options', async () => {
    wrapper = shallowWithContexts(
      <WorkflowApprovalControls
        selected={mockApprovalList}
        onHandleDeny={onHandleDeny}
        onHandleCancel={onHandleCancel}
        onHandleToggleToolbarKebab={onHandleToggleToolbarKebab}
        isKebabOpen={true}
      />
    );
    expect(wrapper.find('WorkflowApprovalControls')).toHaveLength(1);
    expect(wrapper.find('WorkflowApprovalControls').prop('isKebabOpen')).toBe(
      true
    );
  });
});

describe('<WorkflowApprovalControls/>, full mount', () => {
  let wrapper;
  let onHandleDeny = jest.fn();
  let onHandleCancel = jest.fn();
  let onHandleToggleToolbarKebab = jest.fn();
  let mockApprovalList = mockData.results;
  const cancelButton = 'DropdownItem[ouiaId="workflow-cancel-button"]';
  const denyButton = 'DropdownItem[ouiaId="workflow-deny-button"]';

  test('initially render successfully', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalControls
        selected={[]}
        onHandleDeny={onHandleDeny}
        onHandleCancel={onHandleCancel}
        onHandleToggleToolbarKebab={onHandleToggleToolbarKebab}
        isKebabOpen={false}
      />
    );
    expect(wrapper.find('WorkflowApprovalControls')).toHaveLength(1);
    expect(wrapper.find('WorkflowApprovalControls').prop('isKebabOpen')).toBe(
      false
    );
    expect(wrapper.find('Tooltip').prop('content')).toBe(
      'Select items to approve, deny, or cancel'
    );
  });

  test('should call correct functions', () => {
    wrapper = mountWithContexts(
      <WorkflowApprovalControls
        selected={[mockApprovalList[1], mockApprovalList[2]]}
        onHandleDeny={onHandleDeny}
        onHandleCancel={onHandleCancel}
        onHandleToggleToolbarKebab={onHandleToggleToolbarKebab}
        isKebabOpen={true}
      />
    );
    wrapper.find(denyButton).prop('onClick')();
    expect(onHandleDeny).toHaveBeenCalled();
    wrapper.find(cancelButton).prop('onClick')();
    expect(onHandleCancel).toHaveBeenCalled();
    wrapper.find('DropdownToggle').prop('onToggle')(false);
    expect(onHandleToggleToolbarKebab).toHaveBeenCalledWith(false);
  });
});
