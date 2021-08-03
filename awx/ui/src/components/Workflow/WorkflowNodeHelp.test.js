import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import WorkflowNodeHelp from './WorkflowNodeHelp';

const node = {
  originalNodeObject: {
    identifier: 'Foo',
    summary_fields: {
      job: {
        name: 'Foo Job Template',
        elapsed: 9000,
        status: 'successful',
        type: 'job',
      },
      unified_job_template: {
        name: 'Foo Job Template',
        type: 'job_template',
      },
    },
  },
  unifiedJobTemplate: {
    name: 'Foo Job Template',
    unified_job_type: 'job',
  },
};

describe('WorkflowNodeHelp', () => {
  test('renders the expected content for a completed job template job', () => {
    const wrapper = mountWithContexts(<WorkflowNodeHelp node={node} />);
    expect(wrapper.find('#workflow-node-help-alias').text()).toBe('Foo');
    expect(wrapper.find('#workflow-node-help-name').text()).toBe(
      'Foo Job Template'
    );
    expect(wrapper.find('#workflow-node-help-type').text()).toBe(
      'Job Template'
    );
    expect(wrapper.find('#workflow-node-help-status').text()).toBe(
      'Successful'
    );
    expect(wrapper.find('#workflow-node-help-elapsed').text()).toBe('02:30:00');
  });
});
