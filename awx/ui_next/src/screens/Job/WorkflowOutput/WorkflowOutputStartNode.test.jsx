import React from 'react';
import { mount } from 'enzyme';
import WorkflowOutputStartNode from './WorkflowOutputStartNode';

const nodePositions = {
  1: {
    x: 0,
    y: 0,
  },
};

describe('WorkflowOutputStartNode', () => {
  test('mounts successfully', () => {
    const wrapper = mount(
      <svg>
        <WorkflowOutputStartNode nodePositions={nodePositions} />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
  });
});
