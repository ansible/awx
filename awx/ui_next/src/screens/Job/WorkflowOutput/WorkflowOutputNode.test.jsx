import React from 'react';
import { WorkflowStateContext } from '../../../contexts/Workflow';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowOutputNode from './WorkflowOutputNode';

const nodeWithJT = {
  id: 2,
  originalNodeObject: {
    summary_fields: {
      job: {
        elapsed: 7,
        id: 9000,
        name: 'Automation JT',
        status: 'successful',
        type: 'job',
      },
    },
    unifiedJobTemplate: {
      id: 77,
      name: 'Automation JT',
      unified_job_type: 'job',
    },
  },
};

const nodeWithoutJT = {
  id: 2,
  originalNodeObject: {
    summary_fields: {
      job: {
        elapsed: 7,
        id: 9000,
        name: 'Automation JT 2',
        status: 'successful',
        type: 'job',
      },
    },
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

describe('WorkflowOutputNode', () => {
  test('mounts successfully', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={{ nodePositions }}>
          <WorkflowOutputNode
            mouseEnter={() => {}}
            mouseLeave={() => {}}
            node={nodeWithJT}
          />
        </WorkflowStateContext.Provider>
      </svg>
    );
    expect(wrapper).toHaveLength(1);
  });
  test('node contents displayed correctly when Job and Job Template exist', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={{ nodePositions }}>
          <WorkflowOutputNode
            mouseEnter={() => {}}
            mouseLeave={() => {}}
            node={nodeWithJT}
          />
        </WorkflowStateContext.Provider>
      </svg>
    );
    expect(wrapper.contains(<p>Automation JT</p>)).toEqual(true);
    expect(wrapper.find('WorkflowOutputNode Elapsed').text()).toBe('00:00:07');
  });
  test('node contents displayed correctly when Job Template deleted', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={{ nodePositions }}>
          <WorkflowOutputNode
            mouseEnter={() => {}}
            mouseLeave={() => {}}
            node={nodeWithoutJT}
          />
        </WorkflowStateContext.Provider>
      </svg>
    );
    expect(wrapper.contains(<p>Automation JT 2</p>)).toEqual(true);
    expect(wrapper.find('WorkflowOutputNode Elapsed').text()).toBe('00:00:07');
  });
  test('node contents displayed correctly when Job deleted', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={{ nodePositions }}>
          <WorkflowOutputNode
            mouseEnter={() => {}}
            mouseLeave={() => {}}
            node={{ id: 2 }}
          />
        </WorkflowStateContext.Provider>
      </svg>
    );
    expect(wrapper.text()).toBe('DELETED');
  });
});
