import React from 'react';
import { mount } from 'enzyme';
import { ChipGroup } from '.';

describe('<ChipGroup />', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<ChipGroup />);
    expect(wrapper).toMatchSnapshot();
  });
});
