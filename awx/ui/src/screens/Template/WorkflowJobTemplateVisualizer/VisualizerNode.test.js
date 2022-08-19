import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { JobTemplatesAPI, WorkflowJobTemplateNodesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import VisualizerNode from './VisualizerNode';
import { asyncFlush } from '../../../setupTests';

jest.mock('../../../api/models/JobTemplates');
jest.mock('../../../api/models/WorkflowJobTemplateNodes');

WorkflowJobTemplateNodesAPI.readCredentials.mockResolvedValue({
  data: {
    results: [],
  },
});

const nodeWithJT = {
  id: 2,
  fullUnifiedJobTemplate: {
    id: 77,
    name: 'Automation JT',
    type: 'job_template',
  },
};

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
  nodes: [nodeWithJT],
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
    afterEach(() => {
      jest.clearAllMocks();
    });

    test('Displays unified job template name inside node', () => {
      expect(wrapper.find('NodeResourceName').text()).toBe('Automation JT');
    });

    test('Displays action tooltip on hover and updates help text on hover', () => {
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      wrapper.find('g').simulate('mouseenter');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(1);
      expect(wrapper.find('WorkflowActionTooltipItem').length).toBe(5);
      wrapper.find('g').simulate('mouseleave');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      wrapper.find('foreignObject').first().simulate('mouseenter');
      expect(updateNodeHelp).toHaveBeenCalledWith(nodeWithJT);
      wrapper.find('foreignObject').first().simulate('mouseleave');
      expect(updateNodeHelp).toHaveBeenCalledWith(null);
    });

    test('Add tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('g').simulate('mouseenter');
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

    test('Edit tooltip action hover/click updates help text and dispatches properly', async () => {
      wrapper.find('g').simulate('mouseenter');
      wrapper
        .find('WorkflowActionTooltipItem#node-edit')
        .simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('Edit this node');
      wrapper
        .find('WorkflowActionTooltipItem#node-edit')
        .simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-edit').simulate('click');
      await asyncFlush();
      expect(dispatch).toHaveBeenCalledTimes(2);
      expect(dispatch.mock.calls).toEqual([
        [
          {
            type: 'SET_NODES',
            value: [nodeWithJT],
          },
        ],
        [
          {
            type: 'SET_NODE_TO_EDIT',
            value: nodeWithJT,
          },
        ],
      ]);
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });

    test('Details tooltip action hover/click updates help text and dispatches properly', async () => {
      wrapper.find('g').simulate('mouseenter');
      wrapper
        .find('WorkflowActionTooltipItem#node-details')
        .simulate('mouseenter');
      expect(updateHelpText).toHaveBeenCalledWith('View node details');
      wrapper
        .find('WorkflowActionTooltipItem#node-details')
        .simulate('mouseleave');
      expect(updateHelpText).toHaveBeenCalledWith(null);
      wrapper.find('WorkflowActionTooltipItem#node-details').simulate('click');
      await asyncFlush();
      expect(dispatch).toHaveBeenCalledTimes(2);
      expect(dispatch.mock.calls).toEqual([
        [
          {
            type: 'SET_NODES',
            value: [nodeWithJT],
          },
        ],
        [
          {
            type: 'SET_NODE_TO_VIEW',
            value: nodeWithJT,
          },
        ],
      ]);
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
    });

    test('Link tooltip action hover/click updates help text and dispatches properly', () => {
      wrapper.find('g').simulate('mouseenter');
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
      wrapper.find('g').simulate('mouseenter');
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

    test('Displays correct help text when hovering over node while adding link', () => {
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      wrapper.find('g').simulate('mouseenter');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      expect(updateHelpText).toHaveBeenCalledWith(
        'Click to create a new link to this node.'
      );
      wrapper.find('g').simulate('mouseleave');
      expect(wrapper.find('WorkflowActionTooltip').length).toBe(0);
      expect(updateHelpText).toHaveBeenCalledWith(null);
    });

    test('Dispatches properly when node is clicked', () => {
      wrapper.find('foreignObject').first().simulate('click');
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

  describe('Node with empty string alias', () => {
    test('Displays unified job template name inside node', () => {
      const wrapper = mountWithContexts(
        <svg>
          <WorkflowStateContext.Provider value={mockedContext}>
            <VisualizerNode
              node={{
                id: 2,
                identifier: '',
                fullUnifiedJobTemplate: {
                  name: 'foobar',
                },
              }}
              readOnly={false}
              updateHelpText={() => {}}
              updateNodeHelp={() => {}}
            />
          </WorkflowStateContext.Provider>
        </svg>
      );
      expect(wrapper).toHaveLength(1);
      expect(wrapper.find('NodeResourceName').text()).toBe('foobar');
    });
  });

  describe('Node should display convergence label', () => {
    test('Should display ALL convergence label', async () => {
      const wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider value={mockedContext}>
            <svg>
              <VisualizerNode
                node={{
                  id: 2,
                  originalNodeObject: {
                    all_parents_must_converge: true,
                    always_nodes: [],
                    created: '2020-11-19T21:47:55.278081Z',
                    diff_mode: null,
                    extra_data: {},
                    failure_nodes: [],
                    id: 49,
                    identifier: 'f03b62c5-40f8-49e4-97c3-5bb20c91ec91',
                    inventory: null,
                    job_tags: null,
                    job_type: null,
                    limit: null,
                    modified: '2020-11-19T21:47:55.278156Z',
                    related: {
                      credentials:
                        '/api/v2/workflow_job_template_nodes/49/credentials/',
                    },
                    scm_branch: null,
                    skip_tags: null,
                    success_nodes: [],
                    summary_fields: {
                      workflow_job_template: { id: 15 },
                      unified_job_template: {
                        id: 7,
                        description: '',
                        name: 'Example',
                        unified_job_type: 'job',
                      },
                    },
                    type: 'workflow_job_template_node',
                    unified_job_template: 7,
                    url: '/api/v2/workflow_job_template_nodes/49/',
                    verbosity: null,
                    workflowMakerNodeId: 2,
                    workflow_job_template: 15,
                  },
                }}
                readOnly={false}
                updateHelpText={updateHelpText}
                updateNodeHelp={updateNodeHelp}
              />
            </svg>
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
      expect(wrapper.find('p[data-cy="convergence-label"]').length).toBe(1);
      expect(
        wrapper.find('p[data-cy="convergence-label"]').prop('children')
      ).toEqual('ALL');
    });
  });

  describe('Node without full unified job template', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider value={mockedContext}>
            <svg>
              <VisualizerNode
                node={{
                  id: 2,
                  originalNodeObject: {
                    all_parents_must_converge: false,
                    always_nodes: [],
                    created: '2020-11-19T21:47:55.278081Z',
                    diff_mode: null,
                    extra_data: {},
                    failure_nodes: [],
                    id: 49,
                    identifier: 'f03b62c5-40f8-49e4-97c3-5bb20c91ec91',
                    inventory: null,
                    job_tags: null,
                    job_type: null,
                    limit: null,
                    modified: '2020-11-19T21:47:55.278156Z',
                    related: {
                      credentials:
                        '/api/v2/workflow_job_template_nodes/49/credentials/',
                    },
                    scm_branch: null,
                    skip_tags: null,
                    success_nodes: [],
                    summary_fields: {
                      workflow_job_template: { id: 15 },
                      unified_job_template: {
                        id: 7,
                        description: '',
                        name: 'Example',
                        unified_job_type: 'job',
                      },
                    },
                    type: 'workflow_job_template_node',
                    unified_job_template: 7,
                    url: '/api/v2/workflow_job_template_nodes/49/',
                    verbosity: null,
                    workflowMakerNodeId: 2,
                    workflow_job_template: 15,
                  },
                }}
                readOnly={false}
                updateHelpText={updateHelpText}
                updateNodeHelp={updateNodeHelp}
              />
            </svg>
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });

    test('Attempts to fetch full unified job template on view', async () => {
      wrapper.find('g').simulate('mouseenter');
      await act(async () => {
        wrapper
          .find('WorkflowActionTooltipItem#node-details')
          .simulate('click');
      });
      expect(JobTemplatesAPI.readDetail).toHaveBeenCalledWith(7);
      expect(wrapper.find('p[data-cy="convergence-label"]').length).toBe(0);
    });

    test('Displays error fetching full unified job template', async () => {
      JobTemplatesAPI.readDetail.mockRejectedValueOnce(
        new Error({
          response: {
            config: {
              method: 'get',
              url: '/api/v2/job_templates/7',
            },
            data: 'An error occurred',
            status: 403,
          },
        })
      );
      expect(wrapper.find('AlertModal').length).toBe(0);
      wrapper.find('g').simulate('mouseenter');
      await act(async () => {
        wrapper
          .find('WorkflowActionTooltipItem#node-details')
          .simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('AlertModal').length).toBe(1);
    });

    test('Attempts to fetch credentials on view', async () => {
      JobTemplatesAPI.readDetail.mockResolvedValueOnce({
        data: {
          id: 7,
          name: 'Example',
        },
      });
      wrapper.find('g').simulate('mouseenter');
      await act(async () => {
        wrapper
          .find('WorkflowActionTooltipItem#node-details')
          .simulate('click');
      });
      expect(WorkflowJobTemplateNodesAPI.readCredentials).toHaveBeenCalledWith(
        49
      );
    });
    test('Displays error fetching credentials', async () => {
      JobTemplatesAPI.readDetail.mockResolvedValueOnce({
        data: {
          id: 7,
          name: 'Example',
        },
      });
      WorkflowJobTemplateNodesAPI.readCredentials.mockRejectedValueOnce(
        new Error({
          response: {
            config: {
              method: 'get',
              url: '/api/v2/workflow_job_template_nodes/49/credentials',
            },
            data: 'An error occurred',
            status: 403,
          },
        })
      );
      expect(wrapper.find('AlertModal').length).toBe(0);
      wrapper.find('g').simulate('mouseenter');
      await act(async () => {
        wrapper
          .find('WorkflowActionTooltipItem#node-details')
          .simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('AlertModal').length).toBe(1);
    });
  });
});
