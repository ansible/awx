import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import {
  waitForElement,
  mountWithContexts,
} from '../../../../../../testUtils/enzymeHelpers';
import {
  InventorySourcesAPI,
  JobTemplatesAPI,
  ProjectsAPI,
  WorkflowJobTemplatesAPI,
} from '../../../../../api';
import NodeModal from './NodeModal';

jest.mock('../../../../../api/models/InventorySources');
jest.mock('../../../../../api/models/JobTemplates');
jest.mock('../../../../../api/models/Projects');
jest.mock('../../../../../api/models/WorkflowJobTemplates');

let wrapper;
const dispatch = jest.fn();
const onSave = jest.fn();

describe('NodeModal', () => {
  beforeAll(() => {
    JobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Job Template',
            type: 'job_template',
            url: '/api/v2/job_templates/1',
          },
        ],
      },
    });
    JobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    ProjectsAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Project',
            type: 'project',
            url: '/api/v2/projects/1',
          },
        ],
      },
    });
    ProjectsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    InventorySourcesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Inventory Source',
            type: 'inventory_source',
            url: '/api/v2/inventory_sources/1',
          },
        ],
      },
    });
    InventorySourcesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    WorkflowJobTemplatesAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [
          {
            id: 1,
            name: 'Test Workflow Job Template',
            type: 'workflow_job_template',
            url: '/api/v2/workflow_job_templates/1',
          },
        ],
      },
    });
    WorkflowJobTemplatesAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });
  afterAll(() => {
    jest.clearAllMocks();
  });
  describe('Add new node', () => {
    beforeEach(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider
              value={{
                nodeToEdit: null,
              }}
            >
              <NodeModal askLinkType onSave={onSave} title="Add Node" />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      await waitForElement(wrapper, 'PFWizard');
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('Can successfully create a new job template node', async () => {
      act(() => {
        wrapper.find('#link-type-always').simulate('click');
      });
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      wrapper.update();
      wrapper.find('Radio').simulate('click');
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      expect(onSave).toBeCalledWith(
        {
          id: 1,
          name: 'Test Job Template',
          type: 'job_template',
          url: '/api/v2/job_templates/1',
        },
        'always'
      );
    });

    test('Can successfully create a new project sync node', async () => {
      act(() => {
        wrapper.find('#link-type-failure').simulate('click');
      });
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('AnsibleSelect').prop('onChange')(null, 'project_sync');
      });
      wrapper.update();
      wrapper.find('Radio').simulate('click');
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      expect(onSave).toBeCalledWith(
        {
          id: 1,
          name: 'Test Project',
          type: 'project',
          url: '/api/v2/projects/1',
        },
        'failure'
      );
    });

    test('Can successfully create a new inventory source sync node', async () => {
      act(() => {
        wrapper.find('#link-type-failure').simulate('click');
      });
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('AnsibleSelect').prop('onChange')(
          null,
          'inventory_source_sync'
        );
      });
      wrapper.update();
      wrapper.find('Radio').simulate('click');
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      expect(onSave).toBeCalledWith(
        {
          id: 1,
          name: 'Test Inventory Source',
          type: 'inventory_source',
          url: '/api/v2/inventory_sources/1',
        },
        'failure'
      );
    });

    test('Can successfully create a new workflow job template node', async () => {
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('AnsibleSelect').prop('onChange')(
          null,
          'workflow_job_template'
        );
      });
      wrapper.update();
      wrapper.find('Radio').simulate('click');
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      expect(onSave).toBeCalledWith(
        {
          id: 1,
          name: 'Test Workflow Job Template',
          type: 'workflow_job_template',
          url: '/api/v2/workflow_job_templates/1',
        },
        'success'
      );
    });

    test('Can successfully create a new approval template node', async () => {
      act(() => {
        wrapper.find('#link-type-always').simulate('click');
      });
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('AnsibleSelect').prop('onChange')(null, 'approval');
      });
      wrapper.update();

      await act(async () => {
        wrapper.find('input#approval-name').simulate('change', {
          target: { value: 'Test Approval', name: 'name' },
        });
        wrapper.find('input#approval-description').simulate('change', {
          target: { value: 'Test Approval Description', name: 'description' },
        });
        wrapper.find('input#approval-timeout-minutes').simulate('change', {
          target: { value: 5, name: 'timeoutMinutes' },
        });
      });

      // Updating the minutes and seconds is split to avoid a race condition.
      // They both update the same state variable in the parent so triggering
      // them syncronously creates flakey test results.
      await act(async () => {
        wrapper.find('input#approval-timeout-seconds').simulate('change', {
          target: { value: 30, name: 'timeoutSeconds' },
        });
      });
      wrapper.update();

      expect(wrapper.find('input#approval-name').prop('value')).toBe(
        'Test Approval'
      );
      expect(wrapper.find('input#approval-description').prop('value')).toBe(
        'Test Approval Description'
      );
      expect(wrapper.find('input#approval-timeout-minutes').prop('value')).toBe(
        5
      );
      expect(wrapper.find('input#approval-timeout-seconds').prop('value')).toBe(
        30
      );

      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      expect(onSave).toBeCalledWith(
        {
          description: 'Test Approval Description',
          name: 'Test Approval',
          timeout: 330,
          type: 'workflow_approval_template',
        },
        'always'
      );
    });

    test('Cancel button dispatches as expected', () => {
      wrapper.find('button#cancel-node-modal').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'CANCEL_NODE_MODAL',
      });
    });
  });
  describe('Edit existing node', () => {
    afterEach(() => {
      wrapper.unmount();
    });

    test('Can successfully change project sync node to workflow approval node', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider
              value={{
                nodeToEdit: {
                  id: 2,
                  unifiedJobTemplate: {
                    id: 1,
                    name: 'Test Project',
                    unified_job_type: 'project_update',
                  },
                },
              }}
            >
              <NodeModal
                askLinkType={false}
                onSave={onSave}
                title="Edit Node"
              />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      await waitForElement(wrapper, 'PFWizard');
      expect(wrapper.find('AnsibleSelect').prop('value')).toBe('project_sync');
      await act(async () => {
        wrapper.find('AnsibleSelect').prop('onChange')(null, 'approval');
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('input#approval-name').simulate('change', {
          target: { value: 'Test Approval', name: 'name' },
        });
        wrapper.find('input#approval-description').simulate('change', {
          target: { value: 'Test Approval Description', name: 'description' },
        });
        wrapper.find('input#approval-timeout-minutes').simulate('change', {
          target: { value: 5, name: 'timeoutMinutes' },
        });
      });

      // Updating the minutes and seconds is split to avoid a race condition.
      // They both update the same state variable in the parent so triggering
      // them syncronously creates flakey test results.
      await act(async () => {
        wrapper.find('input#approval-timeout-seconds').simulate('change', {
          target: { value: 30, name: 'timeoutSeconds' },
        });
      });
      wrapper.update();

      expect(wrapper.find('input#approval-name').prop('value')).toBe(
        'Test Approval'
      );
      expect(wrapper.find('input#approval-description').prop('value')).toBe(
        'Test Approval Description'
      );
      expect(wrapper.find('input#approval-timeout-minutes').prop('value')).toBe(
        5
      );
      expect(wrapper.find('input#approval-timeout-seconds').prop('value')).toBe(
        30
      );
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });

      expect(onSave).toBeCalledWith(
        {
          description: 'Test Approval Description',
          name: 'Test Approval',
          timeout: 330,
          type: 'workflow_approval_template',
        },
        null
      );
    });

    test('Can successfully change approval node to workflow job template node', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <WorkflowDispatchContext.Provider value={dispatch}>
            <WorkflowStateContext.Provider
              value={{
                nodeToEdit: {
                  id: 2,
                  unifiedJobTemplate: {
                    id: 1,
                    name: 'Test Approval',
                    description: 'Test Approval Description',
                    unified_job_type: 'workflow_approval',
                    timeout: 0,
                  },
                },
              }}
            >
              <NodeModal
                askLinkType={false}
                onSave={onSave}
                title="Edit Node"
              />
            </WorkflowStateContext.Provider>
          </WorkflowDispatchContext.Provider>
        );
      });
      await waitForElement(wrapper, 'PFWizard');
      expect(wrapper.find('AnsibleSelect').prop('value')).toBe('approval');
      await act(async () => {
        wrapper.find('AnsibleSelect').prop('onChange')(
          null,
          'workflow_job_template'
        );
      });
      wrapper.update();
      wrapper.find('Radio').simulate('click');
      await act(async () => {
        wrapper.find('button#next-node-modal').simulate('click');
      });
      expect(onSave).toBeCalledWith(
        {
          id: 1,
          name: 'Test Workflow Job Template',
          type: 'workflow_job_template',
          url: '/api/v2/workflow_job_templates/1',
        },
        null
      );
    });
  });
});
