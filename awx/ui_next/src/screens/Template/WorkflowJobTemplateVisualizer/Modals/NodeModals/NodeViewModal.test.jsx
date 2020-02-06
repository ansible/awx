import React from 'react';
import { WorkflowDispatchContext } from '@contexts/Workflow';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import NodeViewModal from './NodeViewModal';

let wrapper;
const dispatch = jest.fn();

describe('NodeViewModal', () => {
  test('Close button dispatches as expected', () => {
    wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <NodeViewModal />
      </WorkflowDispatchContext.Provider>
    );
    wrapper.find('TimesIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'SET_NODE_TO_VIEW',
      value: null,
    });
  });
});
