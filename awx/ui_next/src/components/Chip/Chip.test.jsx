import React from 'react';
import { mount } from 'enzyme';
import Chip from './Chip';

describe('Chip', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<Chip />);
    expect(wrapper).toHaveLength(1);
  });
});
