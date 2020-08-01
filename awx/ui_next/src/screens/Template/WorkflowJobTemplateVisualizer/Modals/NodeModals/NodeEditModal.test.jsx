import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import NodeEditModal from './NodeEditModal';

const dispatch = jest.fn();

const nodeResource = {
  id: 448,
  type: 'job_template',
  name: 'Test JT',
};

const workflowContext = {
  nodeToEdit: {
    id: 4,
    unifiedJobTemplate: {
      id: 30,
      name: 'Foo JT',
      type: 'job_template',
    },
  },
};

describe('NodeEditModal', () => {
  test('Node modal confirmation dispatches as expected', () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <NodeEditModal />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    act(() => {
      wrapper.find('NodeModal').prop('onSave')(nodeResource);
    });
    expect(dispatch).toHaveBeenCalledWith({
      type: 'UPDATE_NODE',
      node: {
        nodeResource,
      },
    });
  });
});
