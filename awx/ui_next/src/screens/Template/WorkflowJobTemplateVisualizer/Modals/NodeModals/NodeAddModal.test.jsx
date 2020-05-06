import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import NodeAddModal from './NodeAddModal';

const dispatch = jest.fn();

const nodeResource = {
  id: 448,
  type: 'job_template',
  name: 'Test JT',
};

const workflowContext = {
  addNodeSource: 2,
};

describe('NodeAddModal', () => {
  test('Node modal confirmation dispatches as expected', () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <NodeAddModal />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    act(() => {
      wrapper.find('NodeModal').prop('onSave')(nodeResource, 'success');
    });
    expect(dispatch).toHaveBeenCalledWith({
      type: 'CREATE_NODE',
      node: {
        linkType: 'success',
        nodeResource,
      },
    });
  });
});
