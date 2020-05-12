import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import LinkDeleteModal from './LinkDeleteModal';

let wrapper;
const dispatch = jest.fn();

const workflowContext = {
  linkToDelete: {
    source: {
      id: 2,
    },
    target: {
      id: 3,
    },
    linkType: 'always',
  },
};

describe('LinkDeleteModal', () => {
  beforeAll(() => {
    wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <LinkDeleteModal />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Confirm button dispatches as expected', () => {
    wrapper.find('button#confirm-link-removal').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'DELETE_LINK',
    });
  });

  test('Cancel button dispatches as expected', () => {
    wrapper.find('button#cancel-link-removal').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'SET_LINK_TO_DELETE',
      value: null,
    });
  });

  test('Close button dispatches as expected', () => {
    wrapper.find('TimesIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'SET_LINK_TO_DELETE',
      value: null,
    });
  });
});
