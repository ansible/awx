import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import {
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
} from '../../../api';
import Visualizer from './Visualizer';

jest.mock('../../../api');

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
  beforeAll(() => {
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
    jest.clearAllMocks();
    wrapper.unmount();
    delete window.SVGElement.prototype.getBBox;
    delete window.SVGElement.prototype.getBoundingClientRect;
    delete window.SVGElement.prototype.height;
    delete window.SVGElement.prototype.width;
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
      wrapper
        .find('LinkEditModal')
        .find('AnsibleSelect')
        .prop('onChange')(null, 'success');
    });
    wrapper.find('button#link-confirm').simulate('click');
    expect(wrapper.find('LinkEditModal').length).toBe(0);
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
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
