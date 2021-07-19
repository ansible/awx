import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import WorkflowLegend from './WorkflowLegend';

describe('WorkflowLegend', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<WorkflowLegend onClose={() => {}} />);
    expect(wrapper).toHaveLength(1);
  });
});
