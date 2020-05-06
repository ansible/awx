import React from 'react';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import LinkEditModal from './LinkEditModal';

const dispatch = jest.fn();

const workflowContext = {
  linkToEdit: {
    source: {
      id: 2,
    },
    target: {
      id: 3,
    },
    linkType: 'always',
  },
};

describe('LinkEditModal', () => {
  test('Confirm button dispatches as expected', () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <LinkEditModal />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    wrapper.find('button#link-confirm').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'UPDATE_LINK',
      linkType: 'always',
    });
  });
});
