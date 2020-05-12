import React from 'react';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import LinkAddModal from './LinkAddModal';

const dispatch = jest.fn();

const workflowContext = {
  linkToEdit: null,
};

describe('LinkAddModal', () => {
  test('Confirm button dispatches as expected', () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <LinkAddModal />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    wrapper.find('button#link-confirm').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'CREATE_LINK',
      linkType: 'success',
    });
  });
});
