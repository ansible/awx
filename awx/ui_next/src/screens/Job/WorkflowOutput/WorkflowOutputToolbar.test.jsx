import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowOutputToolbar from './WorkflowOutputToolbar';

let wrapper;
const dispatch = jest.fn();
const job = {
  id: 1,
  status: 'successful',
};
const workflowContext = {
  nodes: [],
  showLegend: false,
  showTools: false,
};

describe('WorkflowOutputToolbar', () => {
  beforeAll(() => {
    const nodes = [
      {
        id: 1,
      },
      {
        id: 2,
      },
      {
        id: 3,
        isDeleted: true,
      },
    ];
    wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={{ ...workflowContext, nodes }}>
          <WorkflowOutputToolbar job={job} />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Shows correct number of nodes', () => {
    // The start node (id=1) and deleted nodes (isDeleted=true) should be ignored
    expect(wrapper.find('Badge').text()).toBe('1');
  });

  test('Toggle Legend button dispatches as expected', () => {
    wrapper.find('CompassIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({ type: 'TOGGLE_LEGEND' });
  });

  test('Toggle Tools button dispatches as expected', () => {
    wrapper.find('WrenchIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({ type: 'TOGGLE_TOOLS' });
  });
});
