import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import WorkflowKey from './WorkflowKey';

describe('WorkflowKey', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<WorkflowKey onClose={() => {}} />);
    expect(wrapper).toHaveLength(1);
  });
});
