import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import VisualizerNode from './VisualizerNode';

const mockedContext = {
  addingLink: false,
  addLinkSourceNode: null,
  nodePositions: {
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
  },
};

const nodeWithJT = {
  id: 2,
  unifiedJobTemplate: {
    id: 77,
    name: 'Automation JT',
    type: 'job_template',
  },
};

const dispatch = jest.fn();
const updateHelpText = jest.fn();
const updateNodeHelp = jest.fn();

describe('VisualizerNode', () => {
  describe('Node with unified job template', () => {
    let wrapper;
    beforeAll(() => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider value={mockedContext}>
            <svg>
              <VisualizerNode
                mouseEnter={() => {}}
                mouseLeave={() => {}}
                node={nodeWithJT}
                readOnly={false}
                updateHelpText={updateHelpText}
                updateNodeHelp={updateNodeHelp}
              />
            </svg>
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('Displays unified job template name inside node', () => {
      expect(wrapper.find('NodeResourceName').text()).toBe('Automation JT');
    });
    test('Displays action tooltip on hover and updates help text on hover', () => {
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      wrapper.find('VisualizerNode').simulate('mouseenter');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(1);
      expect(wrapper.find('WorkflowActionTooltipItem').length).toBe(5);
      wrapper.find('VisualizerNode').simulate('mouseleave');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      wrapper
        .find('foreignObject')
        .first()
        .simulate('mouseenter');
      expect(updateNodeHelp).toHaveBeenCalledWith(nodeWithJT);
      wrapper
        .find('foreignObject')
        .first()
        .simulate('mouseleave');
      expect(updateNodeHelp).toHaveBeenCalledWith(null);
    });

    test('Add tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('VisualizerNode').simulate('mouseenter');
      wrapper.find('WorkflowActionTooltipItem#node-add').simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('Add a new node');
      wrapper.find('WorkflowActionTooltipItem#node-add').simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-add').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'START_ADD_NODE',
        sourceNodeId: 2,
      });
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });

    test('Edit tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('VisualizerNode').simulate('mouseenter');
      wrapper
        .find('WorkflowActionTooltipItem#node-edit')
        .simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('Edit this node');
      wrapper
        .find('WorkflowActionTooltipItem#node-edit')
        .simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-edit').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_EDIT',
        value: nodeWithJT,
      });
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });

    test('Details tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('VisualizerNode').simulate('mouseenter');
      wrapper
        .find('WorkflowActionTooltipItem#node-details')
        .simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('View node details');
      wrapper
        .find('WorkflowActionTooltipItem#node-details')
        .simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-details').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_VIEW',
        value: nodeWithJT,
      });
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });

    test('Link tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('VisualizerNode').simulate('mouseenter');
      wrapper
        .find('WorkflowActionTooltipItem#node-link')
        .simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('Link to an available node');
      wrapper
        .find('WorkflowActionTooltipItem#node-link')
        .simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-link').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SELECT_SOURCE_FOR_LINKING',
        node: nodeWithJT,
      });
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });

    test('Delete tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('VisualizerNode').simulate('mouseenter');
      wrapper
        .find('WorkflowActionTooltipItem#node-delete')
        .simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('Delete this node');
      wrapper
        .find('WorkflowActionTooltipItem#node-delete')
        .simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-delete').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_DELETE',
        value: nodeWithJT,
      });
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });
  });
  describe('Node actions while adding a new link', () => {
    let wrapper;
    beforeAll(() => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              ...mockedContext,
              addingLink: true,
              addLinkSourceNode: 323,
            }}
          >
            <svg>
              <VisualizerNode
                mouseEnter={() => {}}
                mouseLeave={() => {}}
                node={nodeWithJT}
                readOnly={false}
                updateHelpText={updateHelpText}
                updateNodeHelp={updateNodeHelp}
              />
            </svg>
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('Displays correct help text when hovering over node while adding link', () => {
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      wrapper.find('VisualizerNode').simulate('mouseenter');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      expect(updateHelpText).toHaveBeenCalledWith(
        'Click to create a new link to this node.'
      );
      wrapper.find('VisualizerNode').simulate('mouseleave');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      expect(updateHelpText).toHaveBeenCalledWith(null);
    });
    test('Dispatches properly when node is clicked', () => {
      wrapper
        .find('foreignObject')
        .first()
        .simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_ADD_LINK_TARGET_NODE',
        value: nodeWithJT,
      });
    });
  });
  describe('Node without unified job template', () => {
    test('Displays DELETED text inside node when unified job template is missing', () => {
      const wrapper = mountWithContexts(
        <svg>
          <WorkflowStateContext.Provider value={mockedContext}>
            <VisualizerNode
              mouseEnter={() => {}}
              mouseLeave={() => {}}
              node={{
                id: 2,
              }}
              readOnly={false}
              updateHelpText={() => {}}
              updateNodeHelp={() => {}}
            />
          </WorkflowStateContext.Provider>
        </svg>
      );
      expect(wrapper).toHaveLength(1);
      expect(wrapper.find('NodeResourceName').text()).toBe('DELETED');
    });
  });
});
