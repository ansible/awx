import React from 'react';
import { mount } from 'enzyme';
import WorkflowStartNode from './WorkflowStartNode';

const nodePositions = {
  1: {
    x: 0,
    y: 0,
  },
};

describe('WorkflowStartNode', () => {
  test('mounts successfully', () => {
    const wrapper = mount(
      <svg>
        <WorkflowStartNode
          nodePositions={nodePositions}
          showActionTooltip={false}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
  });
  test('tooltip shown on hover', () => {
    const wrapper = mount(
      <svg>
        <WorkflowStartNode nodePositions={nodePositions} showActionTooltip />
      </svg>
    );
    expect(wrapper.find('WorkflowActionTooltip')).toHaveLength(0);
    wrapper.find('WorkflowStartNode').simulate('mouseenter');
    expect(wrapper.find('WorkflowActionTooltip')).toHaveLength(1);
    wrapper.find('WorkflowStartNode').simulate('mouseleave');
    expect(wrapper.find('WorkflowActionTooltip')).toHaveLength(0);
  });
});
