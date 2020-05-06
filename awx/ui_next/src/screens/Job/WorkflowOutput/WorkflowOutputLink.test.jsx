import React from 'react';
import { mount } from 'enzyme';
import { WorkflowStateContext } from '../../../contexts/Workflow';
import WorkflowOutputLink from './WorkflowOutputLink';

const link = {
  source: {
    id: 1,
  },
  target: {
    id: 2,
  },
};

const nodePositions = {
  1: {
    width: 72,
    height: 40,
    x: 0,
    y: 0,
  },
  2: {
    width: 180,
    height: 60,
    x: 282,
    y: 40,
  },
};

describe('WorkflowOutputLink', () => {
  test('mounts successfully', () => {
    const wrapper = mount(
      <svg>
        <WorkflowStateContext.Provider value={{ nodePositions }}>
          <WorkflowOutputLink
            link={link}
            nodePositions={nodePositions}
            mouseEnter={() => {}}
            mouseLeave={() => {}}
          />
        </WorkflowStateContext.Provider>
      </svg>
    );
    expect(wrapper).toHaveLength(1);
  });
});
