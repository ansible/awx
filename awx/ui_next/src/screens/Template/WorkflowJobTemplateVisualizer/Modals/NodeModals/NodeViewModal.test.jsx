import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '@contexts/Workflow';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '@api';
import NodeViewModal from './NodeViewModal';

jest.mock('@api/models/JobTemplates');
jest.mock('@api/models/WorkflowJobTemplates');
WorkflowJobTemplatesAPI.readLaunch.mockResolvedValue({});
WorkflowJobTemplatesAPI.readDetail.mockResolvedValue({});
JobTemplatesAPI.readLaunch.mockResolvedValue({});

const dispatch = jest.fn();

function waitForLoaded(wrapper) {
  return waitForElement(
    wrapper,
    'NodeViewModal',
    el => el.find('ContentLoading').length === 0
  );
}

describe('NodeViewModal', () => {
  describe('Workflow job template node', () => {
    let wrapper;
    const workflowContext = {
      nodeToView: {
        unifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          unified_job_type: 'workflow_job',
          created: '2019-08-08T19:24:05.344276Z',
          modified: '2019-08-08T19:24:18.162949Z',
        },
      },
    };

    beforeAll(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider value={workflowContext}>
              <NodeViewModal />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      waitForLoaded(wrapper);
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('should render prompt detail', () => {
      expect(wrapper.find('PromptDetail').length).toBe(1);
    });

    test('should fetch workflow template launch data', () => {
      expect(JobTemplatesAPI.readLaunch).not.toHaveBeenCalled();
      expect(WorkflowJobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
    });

    test('Close button dispatches as expected', () => {
      wrapper.find('TimesIcon').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_VIEW',
        value: null,
      });
    });

    test('Edit button dispatches as expected', () => {
      wrapper.find('button[aria-label="Edit Node"]').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_VIEW',
        value: null,
      });
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_EDIT',
        value: workflowContext.nodeToView,
      });
    });
  });

  describe('Job template node', () => {
    const workflowContext = {
      nodeToView: {
        unifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          type: 'job_template',
          created: '2019-08-08T19:24:05.344276Z',
          modified: '2019-08-08T19:24:18.162949Z',
        },
      },
    };

    test('should fetch job template launch data', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider value={workflowContext}>
              <NodeViewModal />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      waitForLoaded(wrapper);
      expect(WorkflowJobTemplatesAPI.readLaunch).not.toHaveBeenCalled();
      expect(JobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
      wrapper.unmount();
      jest.clearAllMocks();
    });

    test('should show content error when read call unsuccessful', async () => {
      let wrapper;
      JobTemplatesAPI.readLaunch.mockRejectedValue(new Error({}));
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider value={workflowContext}>
              <NodeViewModal />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      waitForLoaded(wrapper);
      expect(wrapper.find('ContentError').length).toBe(1);
      wrapper.unmount();
      jest.clearAllMocks();
    });
  });

  describe('Project node', () => {
    const workflowContext = {
      nodeToView: {
        unifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          type: 'project_update',
          created: '2019-08-08T19:24:05.344276Z',
          modified: '2019-08-08T19:24:18.162949Z',
        },
      },
    };

    test('should not fetch launch data', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider value={workflowContext}>
              <NodeViewModal />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      waitForLoaded(wrapper);
      expect(WorkflowJobTemplatesAPI.readLaunch).not.toHaveBeenCalled();
      expect(JobTemplatesAPI.readLaunch).not.toHaveBeenCalled();
      wrapper.unmount();
      jest.clearAllMocks();
    });
  });
});
