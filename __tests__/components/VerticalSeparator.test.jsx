import React from 'react';
import { mount } from 'enzyme';

import VerticalSeparator from '../../src/components/VerticalSeparator';

describe('VerticalSeparator', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<VerticalSeparator />);
    expect(wrapper).toHaveLength(1);
  });
});
