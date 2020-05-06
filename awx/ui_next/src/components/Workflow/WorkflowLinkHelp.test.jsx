import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import WorkflowLinkHelp from './WorkflowLinkHelp';

describe('WorkflowLinkHelp', () => {
  test('successfully mounts', () => {
    const wrapper = mountWithContexts(<WorkflowLinkHelp link={{}} />);
    expect(wrapper).toHaveLength(1);
  });
  test('renders the expected content for an on success link', () => {
    const link = {
      linkType: 'success',
    };
    const wrapper = mountWithContexts(<WorkflowLinkHelp link={link} />);
    expect(wrapper.find('#workflow-link-help-type').text()).toBe('On Success');
  });
  test('renders the expected content for an on failure link', () => {
    const link = {
      linkType: 'failure',
    };
    const wrapper = mountWithContexts(<WorkflowLinkHelp link={link} />);
    expect(wrapper.find('#workflow-link-help-type').text()).toBe('On Failure');
  });
  test('renders the expected content for an always link', () => {
    const link = {
      linkType: 'always',
    };
    const wrapper = mountWithContexts(<WorkflowLinkHelp link={link} />);
    expect(wrapper.find('#workflow-link-help-type').text()).toBe('Always');
  });
});
