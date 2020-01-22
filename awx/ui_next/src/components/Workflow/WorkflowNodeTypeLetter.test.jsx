import React from 'react';
import { mount } from 'enzyme';
import { PauseIcon } from '@patternfly/react-icons';
import WorkflowNodeTypeLetter from './WorkflowNodeTypeLetter';

describe('WorkflowNodeTypeLetter', () => {
  test('renders JT when type=job_template', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { type: 'job_template' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('JT');
  });
  test('renders JT when unified_job_type=job', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { unified_job_type: 'job' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('JT');
  });
  test('renders P when type=project', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { type: 'project' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('P');
  });
  test('renders P when unified_job_type=project_update', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { unified_job_type: 'project_update' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('P');
  });
  test('renders I when type=inventory_source', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { type: 'inventory_source' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('I');
  });
  test('renders I when unified_job_type=inventory_update', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{
            unifiedJobTemplate: { unified_job_type: 'inventory_update' },
          }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('I');
  });
  test('renders W when type=workflow_job_template', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { type: 'workflow_job_template' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('W');
  });
  test('renders W when unified_job_type=workflow_job', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { unified_job_type: 'workflow_job' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.text()).toBe('W');
  });
  test('renders puse icon when type=workflow_approval_template', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{ unifiedJobTemplate: { type: 'workflow_approval_template' } }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.containsMatchingElement(<PauseIcon />));
  });
  test('renders W when unified_job_type=workflow_approval', () => {
    const wrapper = mount(
      <svg>
        <WorkflowNodeTypeLetter
          node={{
            unifiedJobTemplate: { unified_job_type: 'workflow_approval' },
          }}
        />
      </svg>
    );
    expect(wrapper).toHaveLength(1);
    expect(wrapper.containsMatchingElement(<PauseIcon />));
  });
});
