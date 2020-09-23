import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import VisualizerToolbar from './VisualizerToolbar';

let wrapper;
const close = jest.fn();
const dispatch = jest.fn();
const save = jest.fn();
const template = {
  id: 1,
  name: 'Test JT',
  summary_fields: {
    user_capabilities: {
      start: true,
    },
  },
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
            hasUnsavedChanges={false}
            readOnly={false}
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

  test('Should display action buttons', () => {
    expect(wrapper.find('CompassIcon')).toHaveLength(1);
    expect(wrapper.find('WrenchIcon')).toHaveLength(1);
    expect(wrapper.find('BookIcon')).toHaveLength(1);
    expect(wrapper.find('RocketIcon')).toHaveLength(1);
    expect(wrapper.find('TrashAltIcon')).toHaveLength(1);
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

  test('Launch button should be hidden when user cannot start workflow', () => {
    const nodes = [
      {
        id: 1,
      },
    ];
    const toolbar = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={{ ...workflowContext, nodes }}>
          <VisualizerToolbar
            onClose={close}
            onSave={save}
            template={{
              ...template,
              summary_fields: {
                user_capabilities: {
                  start: false,
                },
              },
            }}
            hasUnsavedChanges
            readOnly={false}
          />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    expect(toolbar.find('LaunchButton button').length).toBe(0);
  });

  test('Launch button should be disabled when there are unsaved changes', () => {
    expect(wrapper.find('LaunchButton button').prop('disabled')).toEqual(false);
    const nodes = [
      {
        id: 1,
      },
    ];
    const disabledToolbar = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={{ ...workflowContext, nodes }}>
          <VisualizerToolbar
            onClose={close}
            onSave={save}
            template={template}
            hasUnsavedChanges
            readOnly={false}
          />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    expect(
      disabledToolbar.find('LaunchButton button').prop('disabled')
    ).toEqual(true);
  });

  test('Buttons should be hidden when user cannot edit workflow', () => {
    const nodes = [
      {
        id: 1,
      },
    ];
    const toolbar = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={{ ...workflowContext, nodes }}>
          <VisualizerToolbar
            onClose={close}
            onSave={save}
            template={template}
            hasUnsavedChanges={false}
            readOnly
          />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    expect(toolbar.find('#visualizer-delete-all').length).toBe(0);
    expect(toolbar.find('#visualizer-save').length).toBe(0);
  });
});
