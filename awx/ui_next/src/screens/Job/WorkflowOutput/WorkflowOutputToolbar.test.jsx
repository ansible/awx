import React from 'react';
import { WorkflowStateContext } from '@contexts/Workflow';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import WorkflowOutputToolbar from './WorkflowOutputToolbar';

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
  test('mounts successfully', () => {
    const wrapper = mountWithContexts(
      <WorkflowStateContext.Provider value={workflowContext}>
        <WorkflowOutputToolbar job={job} />
      </WorkflowStateContext.Provider>
    );
    expect(wrapper).toHaveLength(1);
  });

  test('shows correct number of nodes', () => {
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
    const wrapper = mountWithContexts(
      <WorkflowStateContext.Provider value={{ ...workflowContext, nodes }}>
        <WorkflowOutputToolbar job={job} />
      </WorkflowStateContext.Provider>
    );
    // The start node (id=1) and deleted nodes (isDeleted=true) should be ignored
    expect(wrapper.find('Badge').text()).toBe('1');
  });
});
