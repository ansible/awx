import React from 'react';
import { mount } from 'enzyme';
import ActionButtonCell from './ActionButtonCell';

describe('ActionButtonCell', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<ActionButtonCell />);
    expect(wrapper).toHaveLength(1);
  });
});
