import React from 'react';
import { shallow } from 'enzyme';
import ActionItem from './ActionItem';

describe('<ActionItem />', () => {
  test('should render child with tooltip', async () => {
    const wrapper = shallow(
      <ActionItem columns={1} tooltip="a tooltip" visible>
        foo
      </ActionItem>
    );

    const tooltip = wrapper.find('Tooltip');
    expect(tooltip.prop('content')).toEqual('a tooltip');
    expect(tooltip.prop('children')).toEqual('foo');
  });

  test('should render null if not visible', async () => {
    const wrapper = shallow(
      <ActionItem columns={1} tooltip="foo">
        <div>foo</div>
      </ActionItem>
    );

    expect(wrapper.find('Tooltip')).toHaveLength(0);
    expect(wrapper.find('div')).toHaveLength(0);
    expect(wrapper.text()).toEqual('');
  });
});
