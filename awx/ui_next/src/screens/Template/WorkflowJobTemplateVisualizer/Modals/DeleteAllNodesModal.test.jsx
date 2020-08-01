import React from 'react';
import { WorkflowDispatchContext } from '../../../../contexts/Workflow';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import DeleteAllNodesModal from './DeleteAllNodesModal';

let wrapper;
const dispatch = jest.fn();

describe('DeleteAllNodesModal', () => {
  beforeAll(() => {
    wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <DeleteAllNodesModal />
      </WorkflowDispatchContext.Provider>
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Delete All button dispatches as expected', () => {
    wrapper.find('button#confirm-delete-all-nodes').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'DELETE_ALL_NODES',
    });
  });

  test('Cancel button dispatches as expected', () => {
    wrapper.find('button#cancel-delete-all-nodes').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'TOGGLE_DELETE_ALL_NODES_MODAL',
    });
  });

  test('Close button dispatches as expected', () => {
    wrapper.find('TimesIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'TOGGLE_DELETE_ALL_NODES_MODAL',
    });
  });
});
