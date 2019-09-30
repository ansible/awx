import React from 'react';
import { mount } from 'enzyme';
import ListActionButton from './ListActionButton';

describe('ListActionButton', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<ListActionButton />);
    expect(wrapper).toHaveLength(1);
  });
});
