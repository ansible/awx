import React from 'react';
import { shallow } from 'enzyme';
import SelectableCard from './SelectableCard';

describe('<SelectableCard />', () => {
  let wrapper;
  const onClick = jest.fn();
  test('initially renders without crashing when not selected', () => {
    wrapper = shallow(<SelectableCard onClick={onClick} />);
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
  test('initially renders without crashing when selected', () => {
    wrapper = shallow(<SelectableCard isSelected onClick={onClick} />);
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });
});
