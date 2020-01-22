import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import WorkflowOutputToolbar from './WorkflowOutputToolbar';

const job = {
  id: 1,
  status: 'successful',
};

describe('WorkflowOutputToolbar', () => {
  test('mounts successfully', () => {
    const wrapper = mountWithContexts(
      <WorkflowOutputToolbar
        job={job}
        keyShown={false}
        nodes={[]}
        onKeyToggle={() => {}}
        onToolsToggle={() => {}}
        toolsShown={false}
      />
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
      <WorkflowOutputToolbar
        job={job}
        keyShown={false}
        nodes={nodes}
        onKeyToggle={() => {}}
        onToolsToggle={() => {}}
        toolsShown={false}
      />
    );
    // The start node (id=1) and deleted nodes (isDeleted=true) should be ignored
    expect(wrapper.find('Badge').text()).toBe('1');
  });
});
