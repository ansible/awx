import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import VisualizerLink from './VisualizerLink';

const link = {
  source: {
    id: 2,
  },
  target: {
    id: 3,
  },
  linkType: 'success',
};

const mockedContext = {
  addingLink: false,
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
    3: {
      width: 180,
      height: 60,
      x: 564,
      y: 40,
    },
  },
};

const dispatch = jest.fn();
const updateHelpText = jest.fn();
const updateLinkHelp = jest.fn();

describe('VisualizerLink', () => {
  let wrapper;
  beforeAll(() => {
    wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={mockedContext}>
          <svg>
            <VisualizerLink
              link={link}
              readOnly={false}
              updateHelpText={updateHelpText}
              updateLinkHelp={updateLinkHelp}
            />
          </svg>
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
  });
  afterAll(() => {
    wrapper.unmount();
  });

  test('Displays action tooltip on hover and updates help text on hover', () => {
    expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    wrapper
      .find('g')
      .first()
      .simulate('mouseenter');
    expect(wrapper.find('WorkflowActionTooltip').length).toBe(1);
    expect(wrapper.find('WorkflowActionTooltipItem').length).toBe(3);
    wrapper
      .find('g')
      .first()
      .simulate('mouseleave');
    expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    wrapper
      .find('#link-2-3-overlay')
      .first()
      .simulate('mouseenter');
    expect(updateLinkHelp).toHaveBeenCalledWith(link);
    wrapper
      .find('#link-2-3-overlay')
      .first()
      .simulate('mouseleave');
    expect(updateLinkHelp).toHaveBeenCalledWith(null);
  });

  test('Add Node tooltip action hover/click updates help text and dispatches properly', () => {
    wrapper
      .find('g')
      .first()
      .simulate('mouseenter');
    wrapper
      .find('WorkflowActionTooltipItem#link-add-node')
      .simulate('mouseenter');
    expect(updateHelpText).toHaveBeenCalledWith(
      'Add a new node between these two nodes'
    );
    wrapper
      .find('WorkflowActionTooltipItem#link-add-node')
      .simulate('mouseleave');
    expect(updateHelpText).toHaveBeenCalledWith(null);
    wrapper.find('WorkflowActionTooltipItem#link-add-node').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'START_ADD_NODE',
      sourceNodeId: 2,
      targetNodeId: 3,
    });
    expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
  });

  test('Edit tooltip action hover/click updates help text and dispatches properly', () => {
    wrapper
      .find('g')
      .first()
      .simulate('mouseenter');
    wrapper.find('WorkflowActionTooltipItem#link-edit').simulate('mouseenter');
    expect(updateHelpText).toHaveBeenCalledWith('Edit this link');
    wrapper.find('WorkflowActionTooltipItem#link-edit').simulate('mouseleave');
    expect(updateHelpText).toHaveBeenCalledWith(null);
    wrapper.find('WorkflowActionTooltipItem#link-edit').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'SET_LINK_TO_EDIT',
      value: link,
    });
    expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
  });

  test('Delete tooltip action hover/click updates help text and dispatches properly', () => {
    wrapper
      .find('g')
      .first()
      .simulate('mouseenter');
    wrapper
      .find('WorkflowActionTooltipItem#link-delete')
      .simulate('mouseenter');
    expect(updateHelpText).toHaveBeenCalledWith('Delete this link');
    wrapper
      .find('WorkflowActionTooltipItem#link-delete')
      .simulate('mouseleave');
    expect(updateHelpText).toHaveBeenCalledWith(null);
    wrapper.find('WorkflowActionTooltipItem#link-delete').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'START_DELETE_LINK',
      link,
    });
    expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
  });
});
