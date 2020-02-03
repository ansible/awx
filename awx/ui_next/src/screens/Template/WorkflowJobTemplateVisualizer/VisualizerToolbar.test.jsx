import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '@contexts/Workflow';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import VisualizerToolbar from './VisualizerToolbar';

let wrapper;
const close = jest.fn();
const dispatch = jest.fn();
const save = jest.fn();
const template = {
  id: 1,
  name: 'Test JT',
};
const workflowContext = {
  nodes: [],
  showLegend: false,
  showTools: false,
};

describe('VisualizerToolbar', () => {
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
          <VisualizerToolbar
            onClose={close}
            onSave={save}
            template={template}
          />
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

  test('Delete All button dispatches as expected', () => {
    wrapper.find('TrashAltIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'SET_SHOW_DELETE_ALL_NODES_MODAL',
      value: true,
    });
  });

  test('Delete All button dispatches as expected', () => {
    wrapper.find('TrashAltIcon').simulate('click');
    expect(dispatch).toHaveBeenCalledWith({
      type: 'SET_SHOW_DELETE_ALL_NODES_MODAL',
      value: true,
    });
  });

  test('Save button calls expected function', () => {
    wrapper.find('button[aria-label="Save"]').simulate('click');
    expect(save).toHaveBeenCalled();
  });

  test('Close button calls expected function', () => {
    wrapper.find('TimesIcon').simulate('click');
    expect(close).toHaveBeenCalled();
  });
});
