import React from 'react';
import { mount } from 'enzyme';

import VerticalSeparator from './VerticalSeparator';

describe('VerticalSeparator', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<VerticalSeparator />);
    expect(wrapper).toHaveLength(1);
  });
});
