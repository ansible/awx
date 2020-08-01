import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { WorkflowStateContext } from '../../../contexts/Workflow';
import VisualizerGraph from './VisualizerGraph';

const workflowContext = {
  links: [
    {
      source: {
        id: 1,
      },
      target: {
        id: 2,
      },
      linkType: 'always',
    },
    {
      source: {
        id: 1,
      },
      target: {
        id: 5,
      },
      linkType: 'always',
    },
    {
      source: {
        id: 2,
      },
      target: {
        id: 4,
      },
      linkType: 'success',
    },
    {
      source: {
        id: 2,
      },
      target: {
        id: 3,
      },
      linkType: 'always',
    },
    {
      source: {
        id: 5,
      },
      target: {
        id: 3,
      },
      linkType: 'success',
    },
  ],
  nodePositions: {
    1: { label: '', width: 72, height: 40, x: 36, y: 85 },
    2: { label: '', width: 180, height: 60, x: 282, y: 40 },
    3: { label: '', width: 180, height: 60, x: 582, y: 130 },
    4: { label: '', width: 180, height: 60, x: 582, y: 30 },
    5: { label: '', width: 180, height: 60, x: 282, y: 140 },
  },
  nodes: [
    {
      id: 1,
    },
    {
      id: 2,
      unifiedJobTemplate: {
        name: 'Foo JT',
        type: 'job_template',
      },
    },
    {
      id: 3,
    },
    {
      id: 4,
    },
    {
      id: 5,
    },
  ],
  showLegend: false,
  showTools: false,
};

describe('VisualizerGraph', () => {
  beforeAll(() => {
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

  test('mounts successfully', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={workflowContext}>
          <VisualizerGraph readOnly={false} />
        </WorkflowStateContext.Provider>
      </svg>
    );
    expect(wrapper).toHaveLength(1);
  });

  test('tools and legend are shown when flags are true', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider
          value={{ ...workflowContext, showLegend: true, showTools: true }}
        >
          <VisualizerGraph readOnly={false} />
        </WorkflowStateContext.Provider>
      </svg>
    );

    expect(wrapper.find('WorkflowLegend')).toHaveLength(1);
    expect(wrapper.find('WorkflowTools')).toHaveLength(1);
  });

  test('nodes and links are properly rendered', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={workflowContext}>
          <VisualizerGraph readOnly={false} />
        </WorkflowStateContext.Provider>
      </svg>
    );

    expect(wrapper.find('WorkflowStartNode')).toHaveLength(1);
    expect(wrapper.find('VisualizerNode')).toHaveLength(4);
    expect(wrapper.find('VisualizerLink')).toHaveLength(5);
    expect(wrapper.find('g#link-2-4')).toHaveLength(1);
    expect(wrapper.find('g#link-2-3')).toHaveLength(1);
    expect(wrapper.find('g#link-5-3')).toHaveLength(1);
    expect(wrapper.find('g#link-1-2')).toHaveLength(1);
    expect(wrapper.find('g#link-1-5')).toHaveLength(1);
  });

  test('proper help text is shown when hovering over nodes', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={workflowContext}>
          <VisualizerGraph readOnly={false} />
        </WorkflowStateContext.Provider>
      </svg>
    );

    expect(wrapper.find('WorkflowNodeHelp')).toHaveLength(0);
    expect(wrapper.find('WorkflowLinkHelp')).toHaveLength(0);
    wrapper
      .find('g#node-2')
      .find('foreignObject')
      .first()
      .simulate('mouseenter');
    expect(wrapper.find('WorkflowNodeHelp')).toHaveLength(1);
    expect(wrapper.find('WorkflowNodeHelp').contains(<b>Name</b>)).toEqual(
      true
    );
    expect(
      wrapper.find('WorkflowNodeHelp').containsMatchingElement(<dd>Foo JT</dd>)
    ).toEqual(true);
    expect(wrapper.find('WorkflowNodeHelp').contains(<b>Type</b>)).toEqual(
      true
    );
    expect(
      wrapper
        .find('WorkflowNodeHelp')
        .containsMatchingElement(<dd>Job Template</dd>)
    ).toEqual(true);
    wrapper
      .find('g#node-2')
      .find('foreignObject')
      .first()
      .simulate('mouseleave');
    expect(wrapper.find('WorkflowNodeHelp')).toHaveLength(0);
  });

  test('proper help text is shown when hovering over links', () => {
    const wrapper = mountWithContexts(
      <svg>
        <WorkflowStateContext.Provider value={workflowContext}>
          <VisualizerGraph readOnly={false} />
        </WorkflowStateContext.Provider>
      </svg>
    );

    wrapper.find('#link-2-3-overlay').simulate('mouseenter');
    expect(wrapper.find('WorkflowLinkHelp')).toHaveLength(1);
    expect(wrapper.find('WorkflowLinkHelp').contains(<b>Run</b>)).toEqual(true);
    expect(
      wrapper.find('WorkflowLinkHelp').containsMatchingElement(<dd>Always</dd>)
    ).toEqual(true);
    wrapper.find('#link-2-3-overlay').simulate('mouseleave');
    expect(wrapper.find('WorkflowLinkHelp')).toHaveLength(0);
  });
});
