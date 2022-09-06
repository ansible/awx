import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  OrganizationsAPI,
  WorkflowApprovalTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
import workflowReducer from 'components/Workflow/workflowReducer';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import Visualizer from './Visualizer';

jest.mock('../../../components/Workflow/workflowReducer');

const realWorkflowReducer = jest.requireActual(
  '../../../components/Workflow/workflowReducer'
).default;

jest.mock('../../../api');

const startNode = {
  id: 1,
  fullUnifiedJobTemplate: {
    name: 'START',
  },
};

const defaultLinks = [
  {
    linkType: 'always',
    source: { id: 1 },
    target: { id: 2 },
  },
];

const template = {
  id: 1,
  name: 'Foo WFJT',
  summary_fields: {
    user_capabilities: {
      edit: true,
      delete: true,
      start: true,
      schedule: true,
      copy: true,
    },
  },
};

const mockWorkflowNodes = [
  {
    id: 8,
    success_nodes: [10],
    failure_nodes: [],
    always_nodes: [9],
    summary_fields: {
      unified_job_template: {
        id: 14,
        name: 'A Playbook',
        type: 'job_template',
      },
    },
  },
  {
    id: 9,
    success_nodes: [],
    failure_nodes: [],
    always_nodes: [],
    summary_fields: {
      unified_job_template: {
        id: 14,
        name: 'A Project Update',
        type: 'project',
      },
    },
  },
  {
    id: 10,
    success_nodes: [],
    failure_nodes: [],
    always_nodes: [],
    summary_fields: {
      unified_job_template: {
        elapsed: 10,
        name: 'An Inventory Source Sync',
        type: 'inventory_source',
      },
    },
  },
  {
    id: 11,
    success_nodes: [9],
    failure_nodes: [],
    always_nodes: [],
    summary_fields: {
      unified_job_template: {
        id: 14,
        name: 'Pause',
        type: 'workflow_approval_template',
      },
    },
  },
];

describe('Visualizer', () => {
  let wrapper;
  beforeEach(() => {
    OrganizationsAPI.read.mockResolvedValue({
      data: {
        count: 1,
        results: [{ id: 1, name: 'Default' }],
      },
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: mockWorkflowNodes.length,
        results: mockWorkflowNodes,
      },
    });
    window.SVGElement.prototype.height = {
      baseVal: {
        value: 100,
      },
    };
    window.SVGElement.prototype.width = {
      baseVal: {
        value: 100,
      },
    };
    window.SVGElement.prototype.getBBox = () => ({
      x: 0,
      y: 0,
      width: 500,
      height: 250,
    });

    window.SVGElement.prototype.getBoundingClientRect = () => ({
      x: 303,
      y: 252.359375,
      width: 1329,
      height: 259.640625,
      top: 252.359375,
      right: 1632,
      bottom: 512,
      left: 303,
    });
  });

  afterAll(() => {
    delete window.SVGElement.prototype.getBBox;
    delete window.SVGElement.prototype.getBoundingClientRect;
    delete window.SVGElement.prototype.height;
    delete window.SVGElement.prototype.width;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    jest.resetModules();
    workflowReducer.mockImplementation(realWorkflowReducer);
  });

  test('Renders successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(wrapper.find('ContentError')).toHaveLength(0);
    expect(wrapper.find('WorkflowStartNode')).toHaveLength(1);
    expect(wrapper.find('VisualizerNode')).toHaveLength(4);
    expect(wrapper.find('VisualizerLink')).toHaveLength(5);
  });

  test('Successfully deletes all nodes', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(wrapper.find('DeleteAllNodesModal').length).toBe(0);
    wrapper.find('TrashAltIcon').simulate('click');
    expect(wrapper.find('DeleteAllNodesModal').length).toBe(1);
    wrapper.find('button#confirm-delete-all-nodes').simulate('click');
    expect(wrapper.find('VisualizerStartScreen')).toHaveLength(1);
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(WorkflowJobTemplateNodesAPI.destroy).toHaveBeenCalledWith(8);
    expect(WorkflowJobTemplateNodesAPI.destroy).toHaveBeenCalledWith(9);
    expect(WorkflowJobTemplateNodesAPI.destroy).toHaveBeenCalledWith(10);
    expect(WorkflowJobTemplateNodesAPI.destroy).toHaveBeenCalledWith(11);
  });

  test('Successfully changes link type', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(wrapper.find('LinkEditModal').length).toBe(0);
    wrapper.find('g#link-2-3').simulate('mouseenter');
    wrapper.find('WorkflowActionTooltipItem#link-edit').simulate('click');
    expect(wrapper.find('LinkEditModal').length).toBe(1);
    act(() => {
      wrapper.find('LinkEditModal').find('AnsibleSelect').prop('onChange')(
        null,
        'success'
      );
    });
    wrapper.find('button#link-confirm').simulate('click');
    expect(wrapper.find('LinkEditModal').length).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    expect(
      WorkflowJobTemplateNodesAPI.disassociateAlwaysNode
    ).toHaveBeenCalledWith(8, 9);
    expect(
      WorkflowJobTemplateNodesAPI.associateSuccessNode
    ).toHaveBeenCalledWith(8, 9);
  });

  test('Start Screen shown when no nodes are present', async () => {
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(wrapper.find('VisualizerStartScreen')).toHaveLength(1);
    expect(
      wrapper.find('ActionButton#visualizer-toggle-tools').props().isDisabled
    ).toBe(true);
    expect(
      wrapper.find('ActionButton#visualizer-toggle-legend').props().isDisabled
    ).toBe(true);
  });

  test('Error shown when saving fails due to node add error', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'PING',
              type: 'job_template',
            },
          },
        ];
        newState.links = defaultLinks;
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplatesAPI.createNode.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(WorkflowJobTemplatesAPI.createNode).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown when saving fails due to node edit error', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            isEdited: true,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'PING',
              type: 'job_template',
            },
            originalNodeObject: {
              id: 9000,
            },
          },
        ];
        newState.links = defaultLinks;
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplateNodesAPI.replace.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(WorkflowJobTemplateNodesAPI.replace).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown when saving fails due to approval template add error', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'Approval',
              timeout: 1000,
              type: 'workflow_approval_template',
            },
          },
        ];
        newState.links = defaultLinks;
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplatesAPI.createNode.mockResolvedValue({
      data: {
        id: 9001,
      },
    });
    WorkflowJobTemplateNodesAPI.createApprovalTemplate.mockRejectedValue(
      new Error()
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(WorkflowJobTemplatesAPI.createNode).toHaveBeenCalledTimes(1);
    expect(
      WorkflowJobTemplateNodesAPI.createApprovalTemplate
    ).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  // TODO: figure out why this test is failing, the scenario passes in the ui
  test('Error shown when saving fails due to approval template edit error', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            isEdited: true,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'Approval',
              timeout: 1000,
              type: 'workflow_approval_template',
            },
            originalNodeObject: {
              id: 9000,
              summary_fields: {
                unified_job_template: {
                  unified_job_type: 'workflow_approval',
                },
              },
            },
          },
        ];
        newState.links = defaultLinks;
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplateNodesAPI.replace.mockResolvedValue({
      data: {
        id: 9000,
        summary_fields: {
          unified_job_template: {
            unified_job_type: 'workflow_approval',
            id: 1,
          },
        },
      },
    });
    WorkflowApprovalTemplatesAPI.update.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(WorkflowJobTemplateNodesAPI.replace).toHaveBeenCalledTimes(1);
    expect(WorkflowApprovalTemplatesAPI.update).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown when saving fails due to node disassociate failure', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'Approval',
              timeout: 1000,
              type: 'workflow_approval_template',
            },
            originalNodeObject: {
              id: 9000,
              summary_fields: {
                unified_job_template: {
                  unified_job_type: 'workflow_approval',
                },
              },
              success_nodes: [],
              failure_nodes: [3],
              always_nodes: [],
            },
            success_nodes: [3],
            failure_nodes: [],
            always_nodes: [],
          },
          {
            id: 3,
            fullUnifiedJobTemplate: {
              id: 4,
              name: 'Approval 2',
              timeout: 1000,
              type: 'workflow_approval_template',
            },
            originalNodeObject: {
              id: 9001,
              summary_fields: {
                unified_job_template: {
                  unified_job_type: 'workflow_approval',
                },
              },
              success_nodes: [],
              failure_nodes: [],
              always_nodes: [],
            },
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [],
          },
        ];
        newState.links = [
          {
            linkType: 'always',
            source: { id: 1 },
            target: { id: 2 },
          },
          {
            linkType: 'success',
            source: { id: 2 },
            target: { id: 3 },
          },
        ];
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplateNodesAPI.disassociateFailuresNode.mockRejectedValue(
      new Error()
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(
      WorkflowJobTemplateNodesAPI.disassociateFailuresNode
    ).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown when saving fails due to node associate failure', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'Approval',
              timeout: 1000,
              type: 'workflow_approval_template',
            },
            originalNodeObject: {
              id: 9000,
              summary_fields: {
                unified_job_template: {
                  unified_job_type: 'workflow_approval',
                },
              },
              success_nodes: [],
              failure_nodes: [3],
              always_nodes: [],
            },
            success_nodes: [3],
            failure_nodes: [],
            always_nodes: [],
          },
          {
            id: 3,
            fullUnifiedJobTemplate: {
              id: 4,
              name: 'Approval 2',
              timeout: 1000,
              type: 'workflow_approval_template',
            },
            originalNodeObject: {
              id: 9001,
              summary_fields: {
                unified_job_template: {
                  unified_job_type: 'workflow_approval',
                },
              },
              success_nodes: [],
              failure_nodes: [],
              always_nodes: [],
            },
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [],
          },
        ];
        newState.links = [
          {
            linkType: 'always',
            source: { id: 1 },
            target: { id: 2 },
          },
          {
            linkType: 'success',
            source: { id: 2 },
            target: { id: 3 },
          },
        ];
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplateNodesAPI.disassociateFailuresNode.mockResolvedValue();
    WorkflowJobTemplateNodesAPI.associateSuccessNode.mockRejectedValue(
      new Error()
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(
      WorkflowJobTemplateNodesAPI.associateSuccessNode
    ).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown when saving fails due to credential disassociate failure', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            isEdited: true,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'Ping',
              type: 'job_template',
            },
            originalNodeObject: {
              id: 9000,
              success_nodes: [],
              failure_nodes: [],
              always_nodes: [],
            },
            originalNodeCredentials: [
              {
                id: 456,
                credential_type: 1,
              },
            ],
            promptValues: {
              credentials: [
                {
                  id: 123,
                  credential_type: 1,
                },
              ],
            },
            launchConfig: {
              defaults: {
                credentials: [
                  {
                    id: 456,
                    credential_type: 1,
                  },
                ],
              },
            },
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [],
          },
        ];
        newState.links = defaultLinks;
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplateNodesAPI.replace.mockResolvedValue();
    WorkflowJobTemplateNodesAPI.disassociateCredentials.mockRejectedValue(
      new Error()
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(
      WorkflowJobTemplateNodesAPI.disassociateCredentials
    ).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown when saving fails due to credential associate failure', async () => {
    workflowReducer.mockImplementation((state) => {
      const newState = {
        ...state,
        isLoading: false,
      };

      if (newState.nodes.length === 0) {
        newState.nodes = [
          startNode,
          {
            id: 2,
            isEdited: true,
            fullUnifiedJobTemplate: {
              id: 3,
              name: 'Ping',
              type: 'job_template',
            },
            originalNodeObject: {
              id: 9000,
              success_nodes: [],
              failure_nodes: [],
              always_nodes: [],
            },
            originalNodeCredentials: [
              {
                id: 456,
                credential_type: 1,
              },
            ],
            promptValues: {
              credentials: [
                {
                  id: 123,
                  credential_type: 1,
                },
              ],
            },
            launchConfig: {
              defaults: {
                credentials: [
                  {
                    id: 456,
                    credential_type: 1,
                  },
                ],
              },
            },
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [],
          },
        ];
        newState.links = defaultLinks;
      }

      return newState;
    });
    WorkflowJobTemplatesAPI.readNodes.mockResolvedValue({
      data: {
        count: 0,
        results: [],
      },
    });
    WorkflowJobTemplateNodesAPI.replace.mockResolvedValue();
    WorkflowJobTemplateNodesAPI.disassociateCredentials.mockResolvedValue();
    WorkflowJobTemplateNodesAPI.associateCredentials.mockRejectedValue(
      new Error()
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(0);
    await act(async () => {
      wrapper.find('Button#visualizer-save').simulate('click');
    });
    wrapper.update();
    expect(
      WorkflowJobTemplateNodesAPI.associateCredentials
    ).toHaveBeenCalledTimes(1);
    expect(
      wrapper.find('AlertModal[title="Error saving the workflow!"]').length
    ).toBe(1);
  });

  test('Error shown to user when error thrown fetching workflow nodes', async () => {
    WorkflowJobTemplatesAPI.readNodes.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <svg>
          <Visualizer template={template} />
        </svg>
      );
    });
    wrapper.update();
    expect(wrapper.find('ContentError')).toHaveLength(1);
  });
});
