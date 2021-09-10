import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../../testUtils/enzymeHelpers';
import NodeViewModal from './NodeViewModal';

jest.mock('../../../../../api');

const waitForLoaded = async (wrapper) =>
  waitForElement(
    wrapper,
    'NodeViewModal',
    (el) => el.find('ContentLoading').length === 0
  );

describe('NodeViewModal', () => {
  let dispatch;

  beforeEach(() => {
    dispatch = jest.fn();
    WorkflowJobTemplatesAPI.readLaunch.mockResolvedValue({});
    WorkflowJobTemplatesAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        type: 'workflow_job_template',
        related: {
          webhook_receiver: '/api/v2/job_templates/7/gitlab/',
        },
      },
    });
    WorkflowJobTemplatesAPI.readWebhookKey.mockResolvedValue({
      data: {
        webhook_key: 'Pim3mRXT0',
      },
    });
    JobTemplatesAPI.readLaunch.mockResolvedValue({});
    JobTemplatesAPI.readInstanceGroups.mockResolvedValue({});
    JobTemplatesAPI.readWebhookKey.mockResolvedValue({});
    JobTemplatesAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        type: 'job_template',
      },
    });
  });

  describe('Workflow job template node', () => {
    let wrapper;
    const workflowContext = {
      nodeToView: {
        fullUnifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          unified_job_type: 'workflow_job',
          created: '2019-08-08T19:24:05.344276Z',
          modified: '2019-08-08T19:24:18.162949Z',
          related: {
            webhook_receiver: '/api/v2/workflow_job_templates/2/github/',
          },
        },
      },
    };

    beforeEach(async () => {
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
      jest.resetAllMocks();
    });

    test('should render prompt detail', () => {
      expect(wrapper.find('PromptDetail').length).toBe(1);
    });

    test('should fetch workflow template launch data', () => {
      expect(JobTemplatesAPI.readLaunch).not.toHaveBeenCalled();
      expect(JobTemplatesAPI.readInstanceGroups).not.toHaveBeenCalled();
      expect(WorkflowJobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
      expect(WorkflowJobTemplatesAPI.readWebhookKey).toHaveBeenCalledWith(1);
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
        fullUnifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          unified_job_type: 'job',
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
      expect(JobTemplatesAPI.readWebhookKey).not.toHaveBeenCalledWith();
      expect(JobTemplatesAPI.readLaunch).toHaveBeenCalledWith(1);
      expect(JobTemplatesAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
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
      jest.clearAllMocks();
    });

    test('edit button should be shown when readOnly prop is false', async () => {
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
      expect(wrapper.find('Button#node-view-edit-button').length).toBe(1);
      jest.clearAllMocks();
    });

    test('edit button should be hidden when readOnly prop is true', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider value={workflowContext}>
              <NodeViewModal readOnly />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      waitForLoaded(wrapper);
      expect(wrapper.find('Button#node-view-edit-button').length).toBe(0);
      jest.clearAllMocks();
    });
  });

  describe('Project node', () => {
    const workflowContext = {
      nodeToView: {
        fullUnifiedJobTemplate: {
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
      expect(JobTemplatesAPI.readInstanceGroups).not.toHaveBeenCalled();
      jest.clearAllMocks();
    });
  });

  describe('Inventory Source node', () => {
    const workflowContext = {
      nodeToView: {
        fullUnifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          type: 'inventory_source',
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
      expect(JobTemplatesAPI.readInstanceGroups).not.toHaveBeenCalled();
      jest.clearAllMocks();
    });
  });

  describe('Approval node', () => {
    const workflowContext = {
      nodeToView: {
        fullUnifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          type: 'workflow_approval_template',
          timeout: 0,
          all_parents_must_converge: false,
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
      expect(JobTemplatesAPI.readInstanceGroups).not.toHaveBeenCalled();
      jest.clearAllMocks();
    });
  });

  describe('Convergence label', () => {
    const workflowContext = {
      nodeToView: {
        fullUnifiedJobTemplate: {
          id: 1,
          name: 'Mock Node',
          description: '',
          type: 'workflow_approval_template',
          timeout: 0,
          all_parents_must_converge: false,
        },
      },
    };

    test('should display "Any" Convergence label', async () => {
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
      expect(wrapper.find('Detail[label="Convergence"] dd').text()).toBe('Any');
      jest.clearAllMocks();
    });
  });
});
