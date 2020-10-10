import React from 'react';
import { WorkflowDispatchContext } from '../../../contexts/Workflow';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import VisualizerStartScreen from './VisualizerStartScreen';

const dispatch = jest.fn();

describe('VisualizerStartScreen', () => {
  test('dispatches properly when start button clicked', () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <VisualizerStartScreen />
      </WorkflowDispatchContext.Provider>
    );
    expect(wrapper).toHaveLength(1);
    wrapper.find('Button').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'START_ADD_NODE',
      sourceNodeId: 1,
    });
  });
  test('start button hidden in read-only mode', () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <VisualizerStartScreen readOnly />
      </WorkflowDispatchContext.Provider>
    );
    expect(wrapper.find('Button').length).toBe(0);
  });
});
