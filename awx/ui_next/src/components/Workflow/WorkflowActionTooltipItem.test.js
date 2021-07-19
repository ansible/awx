import React from 'react';
import { mount } from 'enzyme';
import WorkflowActionTooltipItem from './WorkflowActionTooltipItem';

describe('WorkflowActionTooltipItem', () => {
  test('successfully mounts', () => {
    const wrapper = mount(<WorkflowActionTooltipItem id="node" />);
    expect(wrapper).toHaveLength(1);
  });
});
