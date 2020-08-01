import React from 'react';
import { WorkflowDispatchContext } from '../../../../contexts/Workflow';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import UnsavedChangesModal from './UnsavedChangesModal';

let wrapper;
const dispatch = jest.fn();
const onSaveAndExit = jest.fn();
const onExit = jest.fn();

describe('UnsavedChangesModal', () => {
  beforeAll(() => {
    wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <UnsavedChangesModal onSaveAndExit={onSaveAndExit} onExit={onExit} />
      </WorkflowDispatchContext.Provider>
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Exit Without Saving button dispatches as expected', () => {
    wrapper.find('button#confirm-exit-without-saving').simulate('click');
    expect(onExit).toHaveBeenCalled();
  });

  test('Save and Exit button dispatches as expected', () => {
    wrapper.find('button#confirm-save-and-exit').simulate('click');
    expect(onSaveAndExit).toHaveBeenCalled();
  });

  test('Close button dispatches as expected', () => {
    wrapper.find('TimesIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'TOGGLE_UNSAVED_CHANGES_MODAL',
    });
  });
});
