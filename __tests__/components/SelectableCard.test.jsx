import React from 'react';
import { mount } from 'enzyme';
import SelectableCard from '../../src/components/AddRole/SelectableCard';

describe('<SelectableCard />', () => {
  let wrapper;
  const onClick = jest.fn();
  test('initially renders without crashing when not selected', () => {
    wrapper = mount(
      <SelectableCard
        onClick={onClick}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
  test('initially renders without crashing when selected', () => {
    wrapper = mount(
      <SelectableCard
        isSelected
        onClick={onClick}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
});
