import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../../testUtils/enzymeHelpers';
import NodeAddModal from './NodeAddModal';

const dispatch = jest.fn();

const nodeResource = {
  id: 448,
  type: 'job_template',
  name: 'Test JT',
  summary_fields: {
    credentials: [],
  },
};

const workflowContext = {
  addNodeSource: 2,
};

describe('NodeAddModal', () => {
  test('Node modal confirmation dispatches as expected', async () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <NodeAddModal onSave={() => {}} askLinkType title="Add Node" />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    waitForElement(
      wrapper,
      'WizardNavItem[content="ContentLoading"]',
      (el) => el.length === 0
    );
    await act(async () => {
      wrapper.find('NodeModal').prop('onSave')(
        { linkType: 'success', nodeResource },
        {}
      );
    });

    expect(dispatch).toHaveBeenCalledWith({
      node: {
        all_parents_must_converge: false,
        linkType: 'success',
        nodeResource: {
          id: 448,
          name: 'Test JT',
          summary_fields: { credentials: [] },
          type: 'job_template',
        },
      },
      type: 'CREATE_NODE',
    });
  });
});
