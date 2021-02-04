import React from 'react';
import { act } from 'react-dom/test-utils';
import { WorkflowApprovalsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowApprovalList from './WorkflowApprovalList';
import mockWorkflowApprovals from '../data.workflowApprovals.json';

jest.mock('../../../api');

describe('<WorkflowApprovalList />', () => {
  let wrapper;
  beforeEach(() => {
    WorkflowApprovalsAPI.read.mockResolvedValue({
      data: {
        count: mockWorkflowApprovals.results.length,
        results: mockWorkflowApprovals.results,
      },
    });

    WorkflowApprovalsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should load and render workflow approvals', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    expect(wrapper.find('WorkflowApprovalListItem')).toHaveLength(3);
  });

  test('should select workflow approval when checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(
      wrapper
        .find('WorkflowApprovalListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should select all', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();

    const items = wrapper.find('WorkflowApprovalListItem');
    expect(items).toHaveLength(3);
    items.forEach(item => {
      expect(item.prop('isSelected')).toEqual(true);
    });

    expect(
      wrapper
        .find('WorkflowApprovalListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
  });

  test('should disable delete button', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .at(2)
        .invoke('onSelect')();
    });
    wrapper.update();

    expect(wrapper.find('ToolbarDeleteButton button').prop('disabled')).toEqual(
      true
    );
  });

  test('should call delete api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();

    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });

    expect(WorkflowApprovalsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show deletion error', async () => {
    WorkflowApprovalsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/workflow_approvals/221',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovalList />);
    });
    wrapper.update();
    expect(WorkflowApprovalsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      wrapper
        .find('WorkflowApprovalListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();

    const modal = wrapper.find('Modal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });
});
